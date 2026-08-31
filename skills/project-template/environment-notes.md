# Environment notes: {{ project }}

Durable gotchas. Never clobbered: add and correct as you learn, and delete only when something stops being true. If a fact is still load-bearing in a month, it belongs here, not in the changelog or a handover section.

## Code map

- Where the code lives, the entry points, and the module a new session should read first.

## Data, dashboards, metrics

- Which dashboard or query is the source of truth for the headline number, and the caveat that makes the obvious query wrong.

## Tools and access

- Tool quirks, permissions that are missing, commands that hang, the flag that gates the feature.

## Query pitfalls

- The join that double-counts, the timezone the days are cut in, the filter every metric must carry.