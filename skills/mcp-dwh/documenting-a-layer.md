# Documenting a layer so agents can maintain it

A view layer with more than a handful of views needs its own skill in the skills store: a thin index body plus bundled files that carry the structure, the catalog, the query caveats, the change log, and the session handover. This is the shape that has held up in practice.

## Make the views self-describing first

- Set `description` on every view at create time (grain, purpose, one caveat). `view-list` returns it, and agents read it before querying.
- Describe non-obvious columns with `saved-query-column-annotations-create`. User-set descriptions are protected from automatic enrichment.
- Once the layer is stable, certify the spines in the data catalog (`setting-up-data-catalog`) so agents prefer them over raw tables.

## The layer skill

**Body** (one screen): what the layer covers and the entity flow in one line, the two or three rules that bite hardest before querying, a table of view groups with grain and coverage, the file map, companions, and the maintenance contract.

**Bundled files:**

| File | Carries |
|---|---|
| `architecture.md` | The tiers. A mermaid lineage DAG built from the live `FROM` and `JOIN` clauses, an ER diagram of grains and join keys, a greppable table of every view with grain, materialized or live, cadence, reads, and read-by. Materialization order and worst-case staleness. Record the date it was last verified and how to re-verify: `view-list {search: "<prefix>"}`, then `view-get` each id and read its joins. |
| `views.md` | Per-view column catalog: columns, grain, quirks, and the view ids. |
| `querying.md` | Deep links the views carry, one worked example that traces a single entity end to end, and the query-time caveats specific to this layer. |
| `maintaining.md` | The change-a-view and add-a-column workflows as they apply here, plus the validation gotchas this layer has hit. |
| `gaps.md` | Uncovered events, enrichments, the refactor backlog, and a suggested build order. |
| `recipes/*.sql` | Copy-paste queries, formatted for humans, never inlined into prose. |
| `changelog.md` | One line per change, newest first, as a rolling window with the window stated in its header. |
| `handover.md` | In-flight work, blocked items, next steps. Read first when resuming, overwritten at the end of each session. |

**Paired-update rule:** any view add, repoint, or retire updates `architecture.md`'s DAG and table and `views.md`'s catalog in the same step. Put that sentence in the body's maintenance contract.

## What to write down that people forget

- The join keys and which one each product's events carry.
- Which views are report-anchored versus activity-anchored (a spine limited to entities created in the last N days will show lower counts than an activity base over the same window; both are correct).
- Any deliberate oddity: a cycle avoided by routing through a base, a view that plays two roles in a join, a fallback column with a `_source` companion recording which leg answered.
- The known residuals: facts a view cannot carry and why, so the next person does not re-derive the limitation.
- Which dashboards, alerts, and insights read each view, so retirements go consumer-first.