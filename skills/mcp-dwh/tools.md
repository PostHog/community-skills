# The tool surface

Everything here was read from `info <tool>` on the PostHog MCP. Tool schemas drift: run `info` once per session before you write, and trust it over this file when they disagree.

## Saved-query (view) tools

| Tool | What it does | Notes |
|---|---|---|
| `view-list` | List views with status, `sync_frequency`, columns, `latest_error`, `last_run_at` | `search` filters by name. Use it to find ids; paginated. |
| `view-get` | Full definition by id: query, columns, materialization status, `latest_history_id` | Read before any query change. |
| `view-create` | Create a view. Upserts if the name exists | Takes `name`, `query`, optional `description`, `sync_frequency`, `incremental`, `folder_id`, `is_test`. |
| `view-update` | Change name, query, `description`, `sync_frequency`, or `incremental` | Query changes need `edited_history_id`. Re-infers columns and sets status to `modified`. |
| `view-materialize` | Turn a virtual view into a physical table on a schedule | Default cadence `24hour`; pass `sync_frequency` to choose. Rate limited. |
| `view-unmaterialize` | Drop the physical table and schedule, keep the definition | The schema demands `name` and `query` too: send back exactly what `view-get` returned. Rate limited. |
| `view-run` | Trigger a materialization now | `full_refresh: true` rebuilds an incremental view from scratch. |
| `view-run-history` | Last five run statuses with timestamps | The ground truth for "is it actually running". |
| `view-delete` | Soft-delete | Refused when other views depend on it. |

Adjacent tools worth knowing:

- `saved-query-column-annotations-create` / `-list` — set a description on a view (`column_name: ""`) or on one of its columns. User-set descriptions are protected from automatic enrichment.
- `warehouse-tables-refresh-schema-create` — refresh the stored column snapshot of an imported table. A table whose snapshot has a column with `valid: false` breaks inference for every view over it while `execute-sql` still works.
- `execute-sql` — prototype every view query here first; it is the same HogQL but with looser validation.

## Call shapes

- **Query**: always the object `{"kind": "HogQLQuery", "query": "SELECT ..."}`, never a bare string. Format the SQL multi-line with indentation and `--` comments. The SQL editor renders the stored string verbatim and there is no formatter, so minified SQL is what users will see.
- **Conflict detection**: when `query` changes, `view-get` first and pass its `latest_history_id` as `edited_history_id`. An `incremental`-only or `sync_frequency`-only update does not need it.
- **`sync_frequency` buckets**: `15min`, `30min`, `1hour`, `6hour`, `12hour`, `24hour`, `7day`, `30day`, `never`. The write is bounded by lineage: no faster than the slowest source delivers, no slower than the fastest consumer needs. Out-of-range values are rejected. Views over `events` (a streaming source) have no floor.
- **`incremental`**: `{"enabled": true, "incremental_key": "<advancing column>", "unique_key": ["<row identity columns>"], "lookback_seconds": N}`. `unique_key` must include every `GROUP BY` column and can never be null. See `layering.md` for the rules that only surface at run time.
- **Scopes**: read needs `warehouse_view:read`, writes need `warehouse_view:write`.

## Write-path mechanics

- **A timeout is not a failure.** `view-update` and `view-delete` can time out client-side after about a minute and still commit server-side minutes later. Always `view-get` before retrying. A "query was modified by someone else" on the retry means the first attempt landed.
- **Inference is synchronous.** `view-create` and `view-update` infer the column schema inline. A heavy query (aggregation over an inline union, joins over raw event scans) can fail with "Failed to retrieve types" or time out. Decompose it: materialize the heavy parts as bases and make the view a thin join.
- **`soft_update: true` skips inference and does not apply query edits.** It is for saving drafts only.
- **Materialize and run are rate limited.** When rebuilding a chain, go in dependency order and pace the calls.
- **The auto-description job can wedge a fresh view.** Seconds after `view-create`, a background job may write column descriptions and advance the history token. Every following `view-update` by id, and `view-create` upsert under the same name, can then fail with "modified by someone else" for the session, and a fresh `view-get` does not clear it. Escape: create the corrected view under a new name. Practical rule: prototype in `execute-sql` and get the first create right.
- **Renaming a column needs unmaterialize then materialize.** `view-update` plus `view-run` adds and removes columns on the physical table but keeps the old name on a rename, silently. Renaming the view itself is clean: the physical table keeps its data and cadence, but every view that references the old name breaks until repointed.
- **Success echoes are large.** Write tools return the whole view. If your client truncates the result, the write still succeeded: re-read with `view-get`.