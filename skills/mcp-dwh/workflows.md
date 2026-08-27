# Workflows

Chain `view-get` before every query change and pace rate-limited calls. Log each change in the layer's `changelog.md` (see `documenting-a-layer.md`).

## Create and materialize a view

1. Prototype the SQL with `execute-sql` until the numbers are right. Cross-check one derived flag against the raw table.
2. `view-create {name, query: {kind: "HogQLQuery", query: "..."}, description}` — formatted SQL, a one-sentence description of grain and purpose.
3. Check `columns` in the response for the types you expect.
4. `view-materialize {id, sync_frequency}` if it is a base or spine. Leave rollups and subsets virtual.
5. `view-run-history {id}` until the first run completes, then a `count()` and a `max(<timestamp>)` probe.

## Change a view's query

1. `view-get {id}` → note `latest_history_id`.
2. `view-update {id, query, edited_history_id}`.
3. If materialized: `view-run {id}` to rebuild. A formatting-only edit leaves the data valid; re-run only to clear the `modified` badge.
4. If the change alters a column set that downstream views select, re-run those in dependency order.

## Add a column through a chain

Edit the base, then each spine that carries it, then re-materialize base → spine → chained spine. Live tops pick it up on their next read.

## Rename a column

`view-unmaterialize {id, name, query}` (send back what `view-get` returned) → `view-update` with the new SQL → `view-materialize`. Repoint consumers before the final materialize.

## Rename a view

`view-update {id, name}` → `view-update` each dependent's query to the new name → `view-run` the dependents. Do it in one session; the dependents are broken in between.

## Change cadence

`view-update {id, sync_frequency}` with no query and no `edited_history_id`. A rejection means the target is outside `[slowest source interval, finest consumer demand]`. If a base sits under faster consumers, declare the faster cadence on the base explicitly rather than trusting propagation.

## Debug staleness

In order, stopping at the first answer:

1. `view-run-history {id}` — timestamps once a day when you expected hourly means the node is on the slow tier, whatever `sync_frequency` says.
2. `last_run_at` from `view-list` — cheaper, but can disagree with `view-get`; run history wins.
3. `max(<timestamp col>)` on the view via `execute-sql`. For a base with no timestamp, probe membership: join recent ids from a fresh source and count matches.
4. Only then read `latest_error`, and corroborate: it holds the last failure indefinitely, including transient cluster noise, after later runs succeeded.

A manual `view-run` closes a gap immediately once the cause is fixed.

## Retire a view

1. `view-list` and grep every view's query for the name; `view-delete` refuses if a view depends on it, but insights, alerts, and endpoints do not count as dependencies and will break silently.
2. Retire or repoint those consumers first.
3. `view-delete {id}`.

## Recover from a wedged update

If every `view-update` on a freshly created view fails with "modified by someone else" and `view-get` does not clear it, create the corrected view under a new name, repoint consumers, and delete the wedged one later.