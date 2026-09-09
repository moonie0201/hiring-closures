# Observation history export — product copy (for Polar and the site)

Written 2026-09-10 for the monetisation test in `ops/DECISION.md`. Every sentence below
describes what we observed. None promises "ghost job", "filled", "expired by law" or any
compliance outcome. Category words that trip Polar's review ("job board", "directory",
"hiring tool") are avoided because they are also inaccurate: this is an observation dataset.

## Polar product

**Name:** Job-posting observation history — dated export

**Price:** $49 one-time · file download

**Short description (≤ 160 chars):**
Day-by-day observation records for public job postings on Greenhouse, Lever, Ashby,
Recruitee and Rippling boards: when each posting was seen, and when it stopped being seen.

**Description:**

What you get: one gzipped CSV (and the same rows as JSON Lines) of observation events from
a daily sweep of public applicant-tracking-system boards, plus a schema file and a coverage
table.

Each row is one event for one posting on one day:

| field | meaning |
|---|---|
| `d` | observation day (UTC) |
| `provider` | greenhouse · lever · ashby · recruitee · rippling |
| `company` | the board slug as it appears in the public URL |
| `job_id` | the board API's own id for the posting |
| `ev` | `added` (first seen) or `removed` (no longer served) |
| `t`, `loc`, `dept` | title, location, department as the board published them |
| `url` | the public posting URL |
| `posted` | the board's own posted date, where the board publishes one |
| `verified` | on `removed` rows for Greenhouse/Lever: `true` if the single-posting endpoint also answered 404, `false` if it could not be asked, `null` where no such endpoint exists |

What it is not:

- Not a claim that a role was filled, cancelled, or fake. A posting that stopped being
  served is exactly that. Nothing here infers hiring outcomes.
- Not complete history. Observation starts on the day we began watching a board
  (`tracked_since` in the coverage table). Postings already open on that day carry a
  first-seen date that is a floor, not an age.
- Not a feed. This is a dated snapshot of the archive to the cutoff shown on the coverage
  table. If you want fresh data on a schedule, ask — a recurring option is offered on
  request, not sold blind.
- No personal data. No contact fields, no applicant data, no descriptions.

Coverage at cutoff (see the coverage table on the product page for the exact numbers):
boards watched, per-provider counts, first observation day per board, and the days on
which a board was not measured (absent days are absent, never zero).

Licence: the rows are facts about public postings. We claim no database right in them.
You may use them internally and in derived analysis; redistribution of the raw rows in
whole or substantial part is not licensed. Personio boards are excluded from every public
or sold artefact under that platform's marketplace terms.

Refunds: if the file does not match the coverage table, full refund. Questions answered
within 48 hours.

## Site product page — structure

1. Coverage table first (boards by provider, `tracked_since` histogram, cutoff date,
   unmeasured company-days).
2. Schema table (above).
3. Five sample rows, real, with `company` and `url` intact.
4. "What it is not" block, verbatim.
5. Price and the Polar checkout button. One button. No tiers.
6. Link to the free CC0 company-day aggregates, so the difference is visible: free =
   counts per company per day; paid = the posting-level events behind them.
