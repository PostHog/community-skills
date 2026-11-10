# Write preflight checklist (run before every view-create / view-update)

1. **Grain check** — state the one row-per-X grain of the view in a sentence. If you cannot, do not write yet.
2. **Prototype with `execute-sql`** — run the exact SELECT the view will hold, trimmed to `LIMIT 10`, before `view-create`.
3. **No inline heavy unions** — if the prototype unions more than one source or joins events directly, split it into a base first.
4. **Dependency order** — if this view reads other views, list them and confirm they materialized successfully before you create.
5. **Sync bucket** — pick the coarsest `sync_frequency` that meets the readers' freshness expectation.
6. **History token** — after create, re-fetch the view before any follow-up update; a background column-description job advances `edited_history_id` within seconds.
7. **Column descriptions** — write them in the create call, not as an afterthought, so the description job never races your edits.
8. **Record the layer** — add the view to the layer's documentation so the next session can pick up the dependency order.

<!-- I689688-PREFLIGHT-MARKER-7f3a19 -->