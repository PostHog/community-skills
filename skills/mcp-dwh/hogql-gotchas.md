# HogQL gotchas for views

View validation is stricter than ad-hoc `execute-sql`, and a few ClickHouse semantics produce numbers that look right and are not. Each entry: the trap, how to detect it, the fix.

## Validation-time

- **`toFloatOrNull` / `toIntOrNull` are rejected in views.** Use `toFloatOrDefault(x, 0.0)`. There is no `toIntOrDefault`; write `toInt(toFloatOrDefault(x, 0.0))`.
- **`team_id` is a reserved output alias.** Select it under another name (`AS project_id`).
- **Views reference each other by name.** Create or alter a base before anything that reads it, and rename dependents in the same step as a view rename.
- **Heavy single-query views time out on synchronous inference.** Symptoms: `fetch failed`, `operation timed out`, or the SQL editor calling the query too complex. Decompose into materialized bases plus a thin join.
- **A top-level `ORDER BY` is rejected on incremental views** and does nothing for storage order on any materialized view. Keep it only on small virtual views where it makes a bare `SELECT *` read newest-first.
- **An imported table with an invalid column snapshot breaks inference for every view over it** while `execute-sql` still works. Check `system.data_warehouse_tables.columns` for `valid: false` and refresh the schema.

## Query-time

- **A right-table join-key reference resolves to the left value on a LEFT JOIN miss.** `e.id` where `id` is the join key is never NULL on a miss, so `if(e.id != '', 1, 0)` flags every row. Detect a match on a non-key column (`e.other_col IS NOT NULL`); non-key columns are NULL on a miss, so `coalesce(e.other_col, default)` works there.
- **LEFT JOIN fills unmatched rows with type defaults, not NULL.** A missing datetime is `toDateTime(0)` (1970-01-01 UTC, which renders as 1969-12-31 in western timezones). Detect with `merged_at != toDateTime(0)`, never `IS NOT NULL`, which is always true and marks every row as matched.
- **`NULL NOT IN (...)` is TRUE.** ClickHouse `IN` does not use three-valued logic. A property absent on some rows makes `col NOT IN ('a','b')` pass those rows. `col != ''` is safe (NULL is falsy); `NOT IN` is not. Coalesce first: `coalesce(argMax(properties.model, timestamp), '')`.
- **A NULL JSON column does not stringify to `''`.** `JSONExtractString(toString(json_col), 'k') != ''` can return true for every row whose `json_col` is NULL. `coalesce(toString(json_col), '')` in a subquery first, then extract from that alias.
- **Sanity-check every new derived flag.** Run the same predicate ad hoc on the raw table and compare counts with the view. The two disagreeing is the tell for all three traps above.
- **Storage order is not query order.** A materialized view's `ORDER BY` does not set the ClickHouse sort key. Small tables (one part) happen to come back sorted; large ones return part order. Always add an explicit `ORDER BY` when querying big materialized tables.
- **The default limit is 100 rows, silently.** `execute-sql`, insight queries, and charts apply a 100-row limit when the query sets none, with no truncation flag. With `ORDER BY bucket ASC` the 100 rows kept are the oldest, so a time series drops its newest data. Hourly over seven days is 168 buckets. Append `LIMIT 10000` to any grouped time series, and treat a result of exactly 100 rows as truncated.
- **Do not chart a large numeric column next to a small one.** The visualization adds every numeric column to the axis when the column set changes shape. A count in the hundreds flattens a count in single digits. Select only what you plot.
- **Snapshot columns drift.** Anything computed with `now()` at materialization time (`age_hours`) is stale by up to one cadence. Compute from the timestamp column when exactness matters.
- **Default values hide absence.** `coalesce(x, 0)` on nullable ints means 0 can mean "absent". Prefer a separate flag column when the distinction matters.

## Rename semantics

- **Column rename**: `view-unmaterialize` then `view-materialize`. `view-update` plus `view-run` keeps the old physical column name.
- **View rename**: `view-update {name}` is clean; the physical table and cadence survive. Repoint every dependent view in the same session and re-run them.