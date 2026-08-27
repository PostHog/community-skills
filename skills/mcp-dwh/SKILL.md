---
name: MCP Data Warehouse
description: Build and run a curated layer of PostHog data-warehouse views (saved
  queries) with the view-* MCP tools. Covers the tool contracts (query JSON shape,
  edited_history_id, incremental settings, sync_frequency buckets), write-path mechanics
  (timeouts that still commit, inference limits, rename semantics), how to tier a
  layer (materialized bases, grain spines, live tops, naming, join keys, materialization
  order, declared vs effective cadence, staleness), HogQL traps that give wrong numbers
  silently (LEFT JOIN type defaults, NULL NOT IN, JSON nulls, the 100-row default
  limit), workflows (create, change, add or rename a column, rename a view, change
  cadence, debug staleness, retire), and a template for documenting a layer as its
  own skill. Use when creating or materializing views over MCP, structuring views
  into a layer, debugging a stale view or a wrong number, or changing a schedule.
  Trigger on 'create a view', 'materialize', 'saved query', 'view is stale', 'sync_frequency',
  'warehouse view layer'.
trust_tier: community
tags:
- mcp
- dwh
- warehouse
author_handle: andrewm4894
---

# Managing a warehouse view layer over MCP

Playbook for building and running a curated layer of PostHog data-warehouse views (saved queries) with the `view-*` MCP tools — from one materialized view to a multi-tier layer that dashboards, alerts, and other agents depend on. Distilled from operating a production layer of about fifty views for several months. The body is a thin index; the substance lives in the bundled files.

## The shape in one paragraph

A view layer that stays healthy has **tiers**: raw sources → materialized **bases** (one heavy scan or one union each) → materialized **grain spines** (thin joins, one row per entity) → **live tops** (query-time rollups and subsets with no refresh lag of their own). Every view has exactly one grain and one job, is named by domain and grain, and reads bases rather than raw multi-source unions. Changes flow bases-first, re-materialize in dependency order, and get logged in a lightweight layer skill so the next session (human or agent) can pick up where you left off.

## Files

| File | Read it when |
|---|---|
| `tools.md` | The tool surface: the nine `view-*` tools, column annotations, call shapes (`query` JSON, `edited_history_id`, `incremental`, `sync_frequency` buckets, scopes), and the write-path mechanics that surprise people. Read before any write. |
| `layering.md` | How to structure a layer: tiers, naming, join keys, why bases exist, materialization order, cadence semantics (declared vs effective), staleness math, incremental rules. Read before adding or restructuring views. |
| `hogql-gotchas.md` | View-validation and query-time traps: rejected functions, reserved aliases, LEFT JOIN defaults, `NULL NOT IN`, storage order, the 100-row default limit, rename semantics. Read when a view fails validation or a number looks wrong. |
| `workflows.md` | Step-by-step recipes: create and materialize, change a view, add or rename a column, rename a view, change cadence, debug staleness, retire a view, verify a derived flag. |
| `documenting-a-layer.md` | The template for a per-layer skill (`architecture.md`, `views.md`, `querying.md`, `maintaining.md`, `changelog.md`, `handover.md`, `recipes/`) so agents can maintain the layer, plus the view and column descriptions that make it discoverable. |
| `CHANGELOG.md` | Recent changes to this skill, newest first. |

Pull with `call skill-file-get {"skill_name": "mcp-dwh", "file_path": "<file>"}`.

## The three rules that bite hardest

1. **Prototype the SQL with `execute-sql` before `view-create`, and get it right first time.** Validation for views is stricter than ad-hoc queries, inference on heavy queries can time out, and a background column-description job can advance the view's history token seconds after creation so that follow-up updates fail with "modified by someone else". A correct first create avoids all three.
2. **Judge freshness from `view-run-history` or a `max(<timestamp>)` probe, never from `sync_frequency` or `latest_error`.** `sync_frequency` reads back the declared target, not the effective cadence. `latest_error` is sticky: it keeps the last failure string long after the next run succeeded.
3. **Materialize the heavy scans as bases and keep everything above them a thin join.** A single big query that aggregates over inline unions or scans events with joins will fail inference, time out, or OOM. Bases infer instantly, re-run cheaply, and give the layer one place to encode each source's quirks.

## Companions

- `modeling-warehouse-foundations` — the PostHog-views-vs-dbt decision, the basic create → materialize → schedule loop, star-schema joins. This skill starts where that one ends.
- `auditing-warehouse-view-health` — one-shot triage of failed, stale, or unused materialized views across a project.
- `setting-up-data-catalog` — certifying views and registering canonical metrics on top of a layer once it is stable.
- `modeling-dimension-tables` — slow-changing lookup views that a layer's spines join to.
- `querying-posthog-data` — HogQL syntax and the schema-discovery workflow for reading the views you build.

## Maintaining this skill

Keep this body thin. New tool behavior goes in `tools.md`, new traps in `hogql-gotchas.md`, new recipes in `workflows.md`. Tool schemas drift, so re-run `info <tool>` when refreshing `tools.md` rather than trusting the cached notes. Add a one-line entry to `CHANGELOG.md` on every meaningful change and trim past the window as you write.
