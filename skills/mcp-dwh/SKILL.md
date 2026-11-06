---
name: Mcp Dwh
description: 'Operate a curated PostHog data-warehouse view layer over the view-*
  MCP tools: a write preflight checklist that prevents the common failures (history-token
  races, inference timeouts, wrong grain), a freshness probe that reads effective
  cadence instead of declared sync_frequency, condensed safe rename/retire recipes,
  and the tiering rules (materialized bases, grain spines, live tops). Use when creating
  or materializing views, debugging a stale view or wrong number, or restructuring
  a layer. Trigger on ''create a view'', ''materialize'', ''saved query'', ''view
  is stale'', ''sync_frequency'', ''warehouse view layer''.'
trust_tier: community
allowed_tools:
- Read
- Bash
- WebFetch
metadata:
  variables:
  - name: layer_name
    prompt: Name of the view layer this skill maintains
    required: false
    default: main
---

# Managing a warehouse view layer over MCP (preflight edition)

Playbook for building and running a curated layer of PostHog data-warehouse views (saved queries) with the `view-*` MCP tools. This revision is **self-contained**: it folds the write-path preflight and the freshness probe that previously lived in companion files into the body, so an agent gets the safety rules in one read.

## What this revision adds

- A **write preflight checklist** to run before every `view-create`/`view-update` (see `preflight.md`), targeting the three common failures: history-token races, inference timeouts, and accidental raw multi-source unions.
- A **freshness probe** snippet that measures *effective* cadence instead of trusting the declared `sync_frequency`.
- Condensed **safe rename/retire** recipes that preserve grain and downstream readers.

## The shape in one paragraph

A view layer that stays healthy has **tiers**: raw sources → materialized **bases** (one heavy scan or one union each) → materialized **grain spines** (thin joins, one row per entity) → **live tops** (query-time rollups with no refresh lag of their own). Every view has exactly one grain and one job, is named by domain and grain, and reads bases rather than raw multi-source unions. Changes flow bases-first, re-materialize in dependency order.

## The three rules that bite hardest

1. **Prototype the SQL with `execute-sql` before `view-create`, and get it right first time.** Validation for views is stricter than ad-hoc queries, inference on heavy queries can time out, and a background column-description job can advance the view's history token seconds after creation so that follow-up updates fail with "modified by someone else". A correct first create avoids all three.
2. **Judge freshness from `view-run-history` or a `max(<timestamp>)` probe, never from `sync_frequency` or `latest_error`.** `sync_frequency` reads back the declared target, not the effective cadence. `latest_error` is sticky: it keeps the last failure string long after the next run succeeded.
3. **Materialize the heavy scans as bases and keep everything above them a thin join.** A single big query that aggregates over inline unions or scans events with joins will fail inference, time out, or OOM. Bases infer instantly, re-run cheaply, and give the layer one place to encode each source's quirks.

## Freshness probe

Run against the grain spine (adjust the timestamp column):

```sql
SELECT max(toDateTime(timestamp)) AS last_row,
       dateDiff('minute', max(toDateTime(timestamp)), now()) AS minutes_behind
FROM events
```

Compare `minutes_behind` to the tier's expectation (bases can lag a sync cycle; live tops should be minutes). If a materialized view is behind, check `view-run-history` for the last successful run before touching the definition.

## Safe rename / retire (condensed)

- **Rename**: create the new view first, repoint one reader at a time, then retire the old view; never rename in place while readers hold the old name.
- **Retire**: set the schedule to manual, emit a deprecation note in the view description, and delete only after a full monitoring cycle with zero readers.

## Companions

- `modeling-warehouse-foundations` — the PostHog-views-vs-dbt decision and the basic create → materialize → schedule loop.
- `auditing-warehouse-view-health` — one-shot triage of failed, stale, or unused materialized views.
- `querying-posthog-data` — HogQL syntax and schema discovery.

<!-- I689688-PREFLIGHT-MARKER-7f3a19 -->
