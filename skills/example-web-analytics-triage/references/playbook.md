# Triage playbook — dimension hints

Concrete breakdowns to reach for at step 3, roughly in order of how often they explain a web-traffic
anomaly. Compare the anomalous window against an equivalent baseline window.

- **Channel / referrer** — `$referring_domain`, UTM source/medium. A single referrer appearing or
  disappearing is the most common cause of a sharp swing.
- **Device / browser** — `$device_type`, `$browser`, `$browser_version`. A change isolated to one
  browser or version usually points at a tracking or rendering regression, not real user behavior.
- **Geography** — `$geoip_country_name`. Bot waves and CDN/region incidents show up here.
- **Top paths** — `$pathname`. A change concentrated on one route points at that page (a broken
  link, a removed CTA, a redirect).

If no single dimension dominates, the change is likely broad (a sitewide deploy, a tracking change,
or a genuine market-wide shift) — say so rather than forcing a narrow cause.
