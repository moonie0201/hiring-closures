# observations-2026-09-09 — schema and coverage

Rows: **389,845** events over **12,130** boards, 2026-08-26 → 2026-09-09 (UTC). Personio rows excluded: 12,917.

## Coverage

| provider | events |
|---|---|
| greenhouse | 206,423 |
| lever | 86,979 |
| ashby | 62,430 |
| recruitee | 17,893 |
| rippling | 16,120 |

| event | rows |
|---|---|
| added | 358,761 |
| removed | 25,281 |
| changed | 5,803 |

Boards by the day observation began (`tracked_since`). A posting already open on that day carries a first-seen date that is a floor, not an age:

| tracked_since | boards |
|---|---|
| 2026-08-26 | 338 |
| 2026-08-27 | 1,033 |
| 2026-09-04 | 10,759 |

Events per observation day. A day with few rows is a day on which few boards were measured, not a quiet day; absent company-days are absent, never zero:

| day | events |
|---|---|
| 2026-08-26 | 14,797 |
| 2026-08-27 | 40,066 |
| 2026-08-28 | 3,442 |
| 2026-08-29 | 1,952 |
| 2026-08-30 | 135 |
| 2026-08-31 | 373 |
| 2026-09-01 | 2,341 |
| 2026-09-02 | 2,573 |
| 2026-09-03 | 2,626 |
| 2026-09-04 | 281,360 |
| 2026-09-05 | 11,007 |
| 2026-09-06 | 1,133 |
| 2026-09-07 | 3,880 |
| 2026-09-08 | 9,327 |
| 2026-09-09 | 14,833 |

`verified` on `removed` rows (Greenhouse/Lever single-posting endpoint also 404):

| verified | rows |
|---|---|
| True | 17,807 |
| None | 7,474 |

## Schema

| field | meaning |
|---|---|
| `d` | observation day, UTC |
| `provider` | greenhouse · lever · ashby · recruitee · rippling |
| `company` | board slug as in the public URL |
| `job_id` | the board API's own id |
| `ev` | `added` (first seen) · `removed` (no longer served) · `changed` |
| `t`, `loc`, `dept` | title, location, department as published |
| `url` | public posting URL |
| `posted` | the board's own posted date, where published |
| `verified` | removed rows only: true / false / null (see above) |

## What this is not

Not a claim that a role was filled, cancelled or fake. Not complete history: observation starts at `tracked_since`. Not a feed: a dated snapshot to the cutoff. No personal data.
