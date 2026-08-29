# Pricing

All prices in USD. Orders are taken by email at `mooniegilog@gmail.com` and invoiced on
delivery. No card payment method is available yet — see [Payment](#payment).

## Tiers

| | Aggregate archive | Event feed | Metrics |
|---|---|---|---|
| **Price** | **$49/month** or $490/year | **$199/month** or $1,990/year | **priced on request** |
| Grain | company × day | + job-level events | + per-company derived metrics |
| Fields | `d, provider, company, open, added, removed` | + `job_id, ev, t, loc, dept, url, posted, days_open, changed, verified` — see the [field table](README.md#free-versus-paid) for the `dept` and `verified` caveats | + computed columns, below |
| Depth | full, from 2026-08-26 | full, from 2026-08-26 | full, from 2026-08-26 |
| Availability | shipping | shipping | **built to order** — the metric columns are not yet derived by any code |
| Providers | 6, including Personio and Recruitee | 6 | 6 |
| Delivery | daily, gzipped CSV or JSONL | daily | agreed per order |
| Backfill on first delivery | every day collected to date | every day collected to date | every day collected to date |

**One-time archive export — $900.** Everything in the Event feed, every day collected up to
the delivery date, delivered once. No further updates. Licensed perpetually for the files
delivered, on the same terms as a subscription. Buy this if you want a fixed dataset for a
model or a study rather than a running feed.

**The Metrics tier is priced on request and built to order.** Nothing in the collection or
export code computes these columns today; they are functions of the event feed and would be
derived for a specific order, on an agreed scope and cadence. We say so rather than list a
monthly price for something that does not yet run. The columns under discussion, per
company: closure rate (removed ÷ open, by day and trailing 30 days), median realised
time-to-close of removed postings, repost rate, net change (added − removed), and the same
cuts split by department and by location string. The two lower tiers are exporter output
and ship as written.

## Why these numbers

**Not compute.** A full quarter-watchlist sweep bills $0.0157 and there are four a day, so
a full month runs under **$2** in serverless compute; measured spend since collection began
is **$0.15**. If you are pricing this against your own infrastructure bill, do not buy it.
Build it.

What $49 or $199 buys is two things compute does not:

**1. The days you did not collect.** Collection began 2026-08-26. A `removed` record is the
difference between two snapshots taken on two different days; there is no provider field,
no archive endpoint, and no vendor selling one. If you start collecting tomorrow, your
first closure record is dated the day after tomorrow, and no amount of money buys you
2026-08-26. Every day of subscription is a day you do not have to have already spent.

**2. The parts that are tedious rather than hard.** Six ATS adapters, per-host rate limits
(Rippling's documented ceiling is 100 requests per 10 minutes — 0.16 req/s — which alone
paces a sweep), and four correctness guards that exist because each of them was a real bug:
a failed fetch must not look like a closure; a board must return empty twice before any
removal is emitted; a provider returning empty for over 90% of its companies is discarded
for that run; and a repost under a new posting ID must not be counted as a realised
time-to-close. About 6,200 lines of collection code, and an unattended daily schedule that
cannot miss a day, because a missed day is a permanent hole.

**Per-row arithmetic, so you can compare directly.** These are measured on 2026-08-28, the
first day with a complete snapshot on both sides of the diff, across the five providers in
the free sample: 1,368 companies, 54,735 open postings, 1,676 added, 1,472 removed. The
paid feed adds Personio, and daily volume varies.

| Tier | Volume at that day's rate | Effective unit price |
|---|---|---|
| Aggregate archive $49/mo | 1,368 rows/day ≈ 41,600/month | $0.0012 per company-day row |
| Event feed $199/mo | 3,148 add/remove events/day ≈ 95,800/month | $0.0021 per event |

**Against what else is on the market.** Coresignal's Jobs API entry plan is $49 for 2,500
job credits ($0.0196 per posting) and its packaged datasets start at $1,000/month.
TheirStack is $49 for 1,500 job credits, or $0.109 per company for 90 days of that
company's postings. Fantastic.jobs sells a career-site feed from $95/month. Every one of
them sells **open** postings. None of them sells the day a posting stopped being returned,
because none of them holds a dated snapshot series to derive it from.

There are no volume discounts, no introductory rates, and no list price above these
numbers. What is written here is what is charged.

## Do not buy this if

- **You want posting dates or time-open for currently open roles.** Those are free. One
  unauthenticated call returns Greenhouse `first_published`, Lever `createdAt` (epoch
  milliseconds), or Ashby `publishedAt`. Compute `days_open` yourself and pay nothing.
- **You want the job advertisement text.** We do not collect it, store it, or sell it. The
  body of a job ad is the employer's own copyrighted work; we claim no rights in it and do
  not reproduce it.
- **You want salary data.** Not collected.
- **You want to know why a posting closed.** The data says a posting stopped being
  returned. It does not say anyone was hired, that a role was cancelled, or that anyone
  lost a job. Postings also stop being returned for reasons we cannot observe, including
  reposting under a new ID, board migrations, and provider outages.
- **You need coverage before 2026-08-26.** It does not exist.
- **You need a specific company we do not track.** Check
  [`ats-directory`](https://github.com/moonie0201/ats-directory) first. We can add a board
  to the watchlist, but its history starts the day we add it, not earlier.

## Coverage disclosures

Buyers are owed these before ordering, not after.

- **Recruitee's careers-site API requires an authorization token from 10 February 2027.**
  Recruitee coverage after that date depends on a migration to the XML offer feed that is
  already scheduled.
- **The Rippling endpoint we call is undocumented.** Rippling job board API — v1 endpoint,
  undocumented; the documented v2 API states "a Recruiting Pro subscription is required to
  use this API" and a limit of 100 requests per 10 minutes, which we honour.
- **Rippling postings have no reliable publication date.** Rippling supplies a creation
  date only in a per-job detail call the snapshot does not make, so `days_open` for a
  Rippling posting is measured from the first day we saw it and is a lower bound.
- **Every posting already open on 2026-08-26 has a lower-bound `days_open`** for the same
  reason: we did not observe when it opened.
- **A day we failed to collect is missing, not zero.** Gaps are visible in the data as
  absent dates and are never filled with interpolated rows. The same applies per company: a
  company-day row exists only where that board was actually measured.
- **A board's first observed day marks every posting as `added`.** Most of 2026-08-26 and
  2026-08-27 is first sightings rather than new postings. The first comparable day is
  **2026-08-28**.
- **2026-08-26 covers one of the four shards only** — 385 of 1,574 boards. Full-watchlist
  coverage begins 2026-08-27 (1,573 boards measured).
- **An employer's exclusion request is honoured within 48 hours going forward.** Files
  already delivered are outside our control and we say so rather than pretending otherwise.

## What you are licensed to do

What you buy is a non-exclusive, non-transferable, non-sublicensable licence to use the
delivered data internally, including in derived analytics. Redistribution of the raw rows,
resale, and republication as a public dataset are not licensed. Data is supplied as
observed, with no warranty of accuracy; see the method note in the
[README](README.md#limitations) for what a closure record does and does not mean.

Full terms: [TERMS.md](TERMS.md).

## Payment

Orders are taken by email at `mooniegilog@gmail.com` and invoiced on delivery.

Stripe does not operate in South Korea, where this is operated, and no alternative merchant
of record has been set up. There is no card checkout, no payment link, and no self-serve
signup. When a payment method exists it will be stated here and not before.

## Free tier

[`data/sample/closures-72h.csv`](data/sample/closures-72h.csv) — company-day aggregates, last 72 hours,
five providers, rebuilt daily, CC0. It costs nothing and always will. Use it to check the
schema, the coverage and the shape before you send an email.
