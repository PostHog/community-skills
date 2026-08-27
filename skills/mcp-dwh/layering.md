# Layering a warehouse of views

## Tiers

1. **Raw sources** — `events`, `persons`, imported warehouse tables, other products' tables. Never the place to put logic that two views share.
2. **Bases** (materialized) — one per heavy scan or one per source-table union. Each base does one thing: filter and shape a single source, or `UNION ALL` a few same-shaped tables into one flat, tagged table. All source quirks (type coercion, dedupe, a `source` or `region` tag) are encoded here once.
3. **Aspect bases** (materialized) — one per fact family at the target grain: actions, traces, runs, opens. Each reads events or bases, never other aspect bases.
4. **Grain spines** (materialized) — thin joins over bases, exactly one row per entity. Spines can chain (entity → child entity → grandchild), each carrying the join keys downward.
5. **Live tops** (virtual) — subsets, hourly and daily rollups, funnels. They read spines and bases and add no refresh lag of their own.

## Why bases exist

- **Inference.** Aggregating directly over an inline union of several tables often fails column inference. A flat materialized union infers instantly and consumers aggregate over that.
- **Cost and memory.** A per-event materialization that re-sends cumulative payloads (LLM inputs, session histories) can run to tens of gigabytes for two weeks of data and fail to write. Dedupe to the final row per entity in the base before anything reads it.
- **One place per quirk.** When a source changes shape, you fix the base and every consumer inherits it.

Rule: a view never reads a raw multi-source table directly when a base for it exists.

## Naming and grain

- Prefix everything in one layer with its domain: `<domain>_<thing>`.
- Bases: `<domain>_<source>_base`. Spines: `<domain>_<group>_<grain>` (`orders_order`, `runs_run`). Aspect bases: `<domain>_<group>_<aspect>` (`orders_order_payments`). Rollups: `_hourly`, `_daily`.
- One grain per view, stated in the view description. Adding a grain dimension to a rollup (a region, a channel) changes the grain and breaks every tile and alert on it; build a sibling instead.
- Name files and views by job, never by type.

## Join keys

Write down the two or three keys that stitch the layer and put them on every spine: the universal entity handle, the work or task key that rides through other products' events, and any natural key that links create and close events (a URL, an external id). When numeric ids can collide across sources (two regions, two imported databases), always pair them with the source tag in joins and `count(DISTINCT ...)`.

Cycle avoidance: if spine B `LEFT JOIN`s spine A, then A must not read B. Route A's need through a base instead.

## Materialization order

Re-materialize in dependency order: union bases → aspect bases → first spine → chained spines → anything the live tops need. `view-materialize` and `view-run` are rate limited, so pace the chain. Live tops need nothing.

## Cadence: declared vs effective

When a project runs per-node DAG schedules, each view declares a target and the DAG computes an **effective cadence** = `min(own declared target, finest consumer demand)`. Consequences:

- A base declaring `24hour` that feeds a `1hour` consumer really refreshes hourly and still reports `24hour`. Do not read `sync_frequency` as a health signal.
- Propagation is not guaranteed on every edge. A base can sit at `24hour` under two hourly consumers and genuinely run once a day, silently stale for hours, while sibling bases propagate fine. Declare the cadence you need on the base explicitly; never rely on lifting.
- If a project reports `sync_frequency_managed_by_dag: true`, a single per-DAG schedule owns cadence and per-view writes are rejected.

Worst-case staleness through a chain is the sum of each hop's cadence plus the source's own sync interval. A fact from an hourly-synced import through a union base, an aspect base, and two spines, all hourly, can take about five hours to surface. Say so in the layer's docs.

## Incremental materialization

`incremental: {enabled, incremental_key, unique_key, lookback_seconds}` upserts rows at or after the watermark (minus lookback) keyed on `unique_key`. Rules that only show up at run time:

- The validator rejects a top-level `ORDER BY` on an incremental view. Drop it; it never set the storage order anyway.
- Old rows are never pruned, so a `now() - 90 DAY` filter stops bounding the table once the view is incremental.
- Each run has a cap on distinct unique keys (on the order of a few million). A very large seed cannot pass; big event-grain views stay full-rebuild.
- `unique key does not identify a single row` means the source holds duplicates. Dedupe in the query (`GROUP BY` the identity, `any()` the rest) and key on the same columns.
- Run errors for incremental views may only surface on the modeling job record, not on the view's `latest_error`. Check run history.
- A changed query shape, or `view-run {full_refresh: true}`, rebuilds from scratch.