#!/usr/bin/env python3
"""Builds docs/ from data/sample/closures-72h.csv. Python 3.12 stdlib only.

    python site/build.py [--blocklist path]

Every number on every page is recomputed from the CSV on each run. The one thing that
survives between runs is docs/daily.jsonl — one line per day, totals plus that day's top
closers and openers — which is how the calendar fills in while the CSV itself only ever
holds the last 72 hours. Nothing here reads the clock, so two runs on the same inputs
produce identical bytes.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DOCS = ROOT / "docs"
CSV = ROOT / "data" / "sample" / "closures-72h.csv"
HISTORY = DOCS / "daily.jsonl"

BASE = "https://moonie0201.github.io/hiring-closures/"
REPO = "https://github.com/moonie0201/hiring-closures"
RAW = "https://raw.githubusercontent.com/moonie0201/hiring-closures/main/data/sample/"
CC0 = "https://creativecommons.org/publicdomain/zero/1.0/"
EMAIL = "mooniegilog@gmail.com"
COLLECTION_START = date(2026, 8, 26)
FIRST_COMPARABLE = "2026-08-28"
FLOOR = 10  # open at window start; below this a closure share is noise
TOP = 50  # rows per index table
TOP_DAY = 10  # rows per per-day list on the calendar
# ponytail: ~3.7 KB of HTML per day; split into calendar-YYYY-MM.html pages if this bites
DAY_SECTIONS = 90  # newest days that get a top-lists section on the calendar
COLUMNS = ("provider", "company", "open", "added", "removed")

PAGES = [  # (file, nav label)
    ("index.html", "Home"),
    ("closing-fastest.html", "Closing fastest"),
    ("calendar.html", "Calendar"),
]

esc = html.escape


def n(x: int) -> str:
    return f"{x:,}"


def signed(x: int) -> str:
    return f"{x:+,}"


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def key(r: dict) -> str:
    return f"{r['provider']}:{r['company']}"


# --- maths -------------------------------------------------------------------------


def load(path: Path = CSV) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["open"] = int(r["open"])
        r["removed"] = int(r["removed"])
        r["added"] = int(r["added"]) if r["added"] != "" else None
    return sorted(rows, key=lambda r: (r["d"], r["provider"], r["company"]))


def measured(rows: list[dict]) -> list[dict]:
    """Rows with a previous-day snapshot. A board's first day is a baseline: `added` is
    empty and nothing on that row may be summed as a flow."""
    return [r for r in rows if r["added"] is not None]


def top(flow: list[dict], field: str, limit: int = TOP_DAY) -> list[dict]:
    ranked = sorted(flow, key=lambda r: (-r[field], r["provider"], r["company"]))
    return [{k: r[k] for k in COLUMNS} for r in ranked[:limit] if r[field] > 0]


def day_summary(rows: list[dict], d: str) -> dict:
    day = [r for r in rows if r["d"] == d]
    flow = measured(day)
    opened = sum(r["added"] for r in flow)
    closed = sum(r["removed"] for r in flow)
    return {
        "d": d,
        "boards": len(day),
        "baseline": len(day) - len(flow),
        "open": sum(r["open"] for r in day),
        "opened": opened,
        "closed": closed,
        "net": opened - closed,
        "closers": top(flow, "removed"),
        "openers": top(flow, "added"),
    }


def window(rows: list[dict]) -> list[dict]:
    """Per company over the days in the file. The first day a company appears sets its
    starting stock; flows are summed over the days after it, so closed ÷ (open at start +
    added after) compares like with like. The first day's own added/removed describe the
    change from a day outside the file and are not used — which also makes a baseline
    row (added empty) harmless wherever it falls."""
    by: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        by.setdefault((r["provider"], r["company"]), []).append(r)
    out = []
    for (provider, company), days in sorted(by.items()):
        first, *after = days  # rows are sorted by d
        added = sum(r["added"] or 0 for r in after)
        closed = sum(r["removed"] for r in after)
        exposure = first["open"] + added
        out.append(
            {
                "provider": provider,
                "company": company,
                "days": len(days),
                "open_start": first["open"],
                "open_end": days[-1]["open"],
                "added": added,
                "closed": closed,
                "net": added - closed,
                "share": closed / exposure if exposure else 0.0,
            }
        )
    return out


TIEBREAK = {"closed": "share", "share": "closed", "net": "added"}


def rank(companies: list[dict], field: str, limit: int = TOP) -> list[dict]:
    """Ties: the secondary field, then provider, then company, all deterministic."""
    eligible = [c for c in companies if c["open_start"] >= FLOOR and c["days"] > 1]
    second = TIEBREAK[field]
    ranked = sorted(
        eligible, key=lambda c: (-c[field], -c[second], c["provider"], c["company"])
    )
    return [c for c in ranked[:limit] if c[field] > 0]


def read_blocklist(path: Path | None) -> frozenset[str]:
    if path is None or not path.exists():
        return frozenset()
    lines = (ln.strip() for ln in path.read_text(encoding="utf-8").splitlines())
    return frozenset(ln for ln in lines if ln and not ln.startswith("#"))


def merge_history(
    rows: list[dict], blocked: frozenset[str] = frozenset()
) -> list[dict]:
    """Days in the CSV overwrite their history line; older days are kept as they were,
    minus any company that has since asked to be removed."""
    days: dict[str, dict] = {}
    if HISTORY.exists():
        for line in HISTORY.read_text(encoding="utf-8").splitlines():
            if line.strip():
                e = json.loads(line)
                days[e["d"]] = e
    for d in sorted({r["d"] for r in rows}):
        days[d] = day_summary(rows, d)
    for e in days.values():
        for k in ("closers", "openers"):
            e[k] = [c for c in e[k] if key(c) not in blocked]
    return [days[d] for d in sorted(days)]


# --- analytics ----------------------------------------------------------------------

#: GA4 measurement id for the Pages site. Cookieless configuration: `client_storage: none`
#: (no _ga cookie, no persistent client id), ad signals and personalisation off. Page views
#: and referrers still arrive, which is all the site needs to learn where readers come from.
GA_ID = "G-3G87HK9EL5"
GA_TAG = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', '{GA_ID}', {{
  'client_storage': 'none',
  'allow_google_signals': false,
  'allow_ad_personalization_signals': false,
  'anonymize_ip': true
}});
</script>
"""

# --- html --------------------------------------------------------------------------

DISCLAIMER = f"""<div class="disclaimer">
<p><strong>Independent.</strong> This is an independent dataset. We are not affiliated with,
endorsed by, or connected to Greenhouse, Lever, Ashby, Recruitee, Rippling, Personio, or any
employer named in it. All trademarks belong to their owners.</p>
<p><strong>What a <code>removed</code> record means.</strong> A job posting that was returned
by a company's public careers API on one day was no longer returned on a later day. It is not
a statement that anyone was hired, that a role was cancelled, or that anyone lost a job.
Postings also stop being returned for reasons we cannot observe, including reposting under a
new ID, board migrations, and provider outages.</p>
<p><strong>A board's first observed day is a baseline, not hiring.</strong> The first time we
see a board, every posting on it is new to the dataset. That day is published with
<code>added</code> empty, and nothing on this site sums it as growth. The first day with
complete snapshots on both sides of the diff is {FIRST_COMPARABLE}.</p>
<p><strong>No job advertisement text, ever.</strong> The body of a job ad is the employer's
own copyrighted work; it is never stored, reproduced, excerpted or summarised, in any tier.
The free file carries no free text at all — no titles, no locations, no URLs.</p>
<p><strong>Measurement.</strong> Page views are counted with Google Analytics in a
cookieless configuration: no analytics cookie is set, no client identifier is stored, IP
addresses are anonymised, and advertising features are off. The only purpose is to see which
pages are read and where readers arrive from.</p>
<p><a href="{REPO}">Repository</a> ·
<a href="https://github.com/moonie0201/ats-directory">Company → ATS directory (CC0)</a> ·
<a href="{CC0}">CC0 1.0</a> ·
<a href="mailto:{EMAIL}">{EMAIL}</a></p>
</div>"""


def url_of(file: str) -> str:
    return BASE + ("" if file == "index.html" else file)


def page(file: str, title: str, description: str, body: str, head: str = "") -> str:
    url = url_of(file)
    links = []
    for f, label in PAGES:
        current = ' aria-current="page"' if f == file else ""
        href = "./" if f == "index.html" else f
        links.append(f'<a href="{href}"{current}>{label}</a>')
    nav = " · ".join(links)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="hiring-closures">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{url}">
<link rel="stylesheet" href="style.css">
{GA_TAG}{head}</head>
<body>
<nav>{nav} · <a href="{RAW}closures-72h.csv">CSV</a> · <a href="{REPO}">Repository</a></nav>
{body}
<footer>
{DISCLAIMER}
</footer>
</body>
</html>
"""


def table(rows: list[dict], cols: list[tuple[str, str, object]]) -> str:
    """cols: (header, css class, formatter(row) -> html)."""
    head = "".join(f'<th class="{c}">{esc(h)}</th>' for h, c, _ in cols)
    body = "".join(
        "<tr>" + "".join(f'<td class="{c}">{f(r)}</td>' for _, c, f in cols) + "</tr>\n"
        for r in rows
    )
    return f'<div class="tw"><table><thead><tr>{head}</tr></thead>\n<tbody>\n{body}</tbody></table></div>'


def numbered(rows: list[dict]) -> list[dict]:
    return [{"rank": i, **r} for i, r in enumerate(rows, 1)]


def company_cols(*extra: tuple[str, str, object]) -> list[tuple[str, str, object]]:
    return [
        ("#", "n", lambda r: str(r["rank"])),
        ("Company", "", lambda r: f"<code>{esc(r['company'])}</code>"),
        ("Provider", "", lambda r: esc(r["provider"])),
        ("Open at start", "n", lambda r: n(r["open_start"])),
        ("Added", "n", lambda r: n(r["added"])),
        ("Closed", "n", lambda r: n(r["closed"])),
        *extra,
        ("Open now", "n", lambda r: n(r["open_end"])),
    ]


def headline(s: dict) -> str:
    base = ""
    if s["baseline"]:
        base = f", {n(s['baseline'])} of them first-day baselines counted here and nowhere else"
    return f"""<section class="stats" aria-label="Latest measured day">
<p class="small muted">Latest measured day, <strong>{s["d"]}</strong>, five-provider free file</p>
<dl>
<div><dt>Postings opened</dt><dd>{n(s["opened"])}</dd></div>
<div><dt>Postings closed</dt><dd>{n(s["closed"])}</dd></div>
<div><dt>Net</dt><dd>{signed(s["net"])}</dd></div>
<div><dt>Boards measured</dt><dd>{n(s["boards"])}</dd></div>
</dl>
<p class="small muted">{n(s["open"])} postings open across those boards{base}. Opened, closed
and net sum only boards with a previous-day snapshot.
<a href="closing-fastest.html">Which companies are closing fastest</a> ·
<a href="calendar.html">every day on record</a>.</p>
</section>"""


def dataset_jsonld(days: list[str]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "hiring-closures: daily job-posting closures across company careers boards",
        "description": (
            "One row per company per day: how many job postings each company's public "
            "careers API returned (open), how many were first seen that day (added) and how "
            "many returned on a previous day were no longer returned (removed). 1,574 "
            "company boards on six ATS platforms (Greenhouse, Lever, Ashby, Recruitee, "
            "Rippling; Personio in paid tiers only), observed daily since 2026-08-26. The "
            "free file is the last 72 hours, six aggregate columns, no job titles, no URLs, "
            "no advertisement text, rebuilt daily and dedicated to the public domain under "
            "CC0 1.0. A removed record means a posting stopped being returned by the API; it "
            "says nothing about hires, cancellations or people."
        ),
        "url": BASE,
        "sameAs": REPO,
        "identifier": REPO,
        "license": CC0,
        "isAccessibleForFree": True,
        "creator": {"@type": "Organization", "name": "hiring-closures", "url": REPO},
        "keywords": [
            "job postings",
            "hiring",
            "job posting closures",
            "applicant tracking systems",
            "labour market",
            "Greenhouse",
            "Lever",
            "Ashby",
            "Recruitee",
            "Rippling",
        ],
        "temporalCoverage": f"{days[0]}/{days[-1]}",
        "dateModified": days[-1],
        "measurementTechnique": (
            "Daily snapshot of each employer's public ATS careers API, diffed against the "
            "previous snapshot; added and removed are counts of posting IDs that appeared "
            "or disappeared between the two."
        ),
        "variableMeasured": [
            {
                "@type": "PropertyValue",
                "name": "d",
                "description": "observation date, UTC",
            },
            {
                "@type": "PropertyValue",
                "name": "provider",
                "description": "ATS platform: greenhouse, lever, ashby, recruitee, rippling",
            },
            {
                "@type": "PropertyValue",
                "name": "company",
                "description": "the ATS board slug, verbatim",
            },
            {
                "@type": "PropertyValue",
                "name": "open",
                "description": "postings the board returned that day",
            },
            {
                "@type": "PropertyValue",
                "name": "added",
                "description": (
                    "postings first seen that day; empty on a board's first observed day"
                ),
            },
            {
                "@type": "PropertyValue",
                "name": "removed",
                "description": (
                    "postings returned on a previous day and not returned that day"
                ),
            },
        ],
        "distribution": [
            {
                "@type": "DataDownload",
                "encodingFormat": "text/csv",
                "contentUrl": RAW + "closures-72h.csv",
            },
            {
                "@type": "DataDownload",
                "encodingFormat": "application/x-ndjson",
                "contentUrl": RAW + "closures-72h.jsonl",
            },
        ],
    }
    body = json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True)
    return f'<script type="application/ld+json">\n{body}\n</script>\n'


def index_page(latest: dict, days: list[str]) -> str:
    landing = (SITE / "landing.html").read_text(encoding="utf-8")
    body = landing.replace("<!--HEADLINE-->", headline(latest), 1)
    return page(
        "index.html",
        "hiring-closures — when job postings disappear",
        "A daily record of when job postings stop being returned by company careers APIs. "
        "1,574 company boards, six ATS platforms, daily since 2026-08-26. Free 72-hour "
        "sample under CC0.",
        body,
        head=dataset_jsonld(days),
    )


def closing_page(companies: list[dict], days: list[str]) -> str:
    start, end = days[0], days[-1]
    share_col = ("Closure share", "n", lambda r: pct(r["share"]))
    net_col = ("Net", "n", lambda r: signed(r["net"]))
    by_closed = numbered(rank(companies, "closed"))
    by_share = numbered(rank(companies, "share"))
    by_net = numbered(rank(companies, "net"))
    eligible = sum(1 for c in companies if c["open_start"] >= FLOOR and c["days"] > 1)
    # A board that went to zero has its company-day dropped from the file (README), so the
    # chain breaks for it when it returns; say so rather than publish a false sentence.
    bad = [
        c
        for c in companies
        if c["open_end"] != c["open_start"] + c["added"] - c["closed"]
    ]
    exceptions = (
        " except "
        + ", ".join(f"<code>{esc(key(c))}</code>" for c in bad)
        + " (a day inside the window is missing from the file)"
        if bad
        else ""
    )
    body = f"""<h1>Which companies are closing job postings fastest?</h1>
<p class="lede">Ranked from the free file: every board measured in the five-provider
free file, stock measured on <strong>{start}</strong>, changes through
<strong>{end}</strong>. Rebuilt daily as the 72-hour window rolls forward.</p>

<div class="note">
<p><strong>How every number here is computed.</strong> For each company, the first day it
appears in the file sets <em>open at start</em>. Over the days after it, <em>added</em> is
the sum of <code>added</code> and <em>closed</em> the sum of <code>removed</code>; the first
day's own <code>added</code>/<code>removed</code> describe the change from a day outside the
file and are not used, which is also what keeps a first-day baseline (<code>added</code>
empty) out of every sum. <strong>Closure share = closed ÷ (open at start + added)</strong>:
the fraction of every posting that was on the board at any point in the window and was
gone by the end. <em>Net</em> = added − closed, and <em>open now</em> = open at start + added
− closed holds for every row in this build{exceptions}. Only boards with <strong>at least {FLOOR} postings
open at the start</strong> and measured on more than one day are ranked ({n(eligible)} of
{n(len(companies))} boards); below that a share is noise. Ties are broken by the secondary
column, then provider, then company, so the order is reproducible.</p>
</div>

<h2 id="closed">Most postings closed</h2>
<p class="small muted">Top {len(by_closed)} by postings closed; ties by closure share.</p>
{table(by_closed, company_cols(share_col))}

<h2 id="share">Highest closure share</h2>
<p class="small muted">Top {len(by_share)} by closure share; ties by postings closed. A high
share on a small board can be a board migration or a repost under new IDs — see the
disclaimer below.</p>
{table(by_share, company_cols(share_col))}

<h2 id="growth">Largest net growth</h2>
<p class="small muted">Top {len(by_net)} by net (added − closed); ties by postings added.</p>
{table(by_net, company_cols(net_col))}

<h2 id="cite">How to cite</h2>
<p>The page and the data behind it are public domain (CC0 1.0). Cite the page by its
canonical URL and the date range, and the file by its raw URL — the file is rebuilt daily,
so a copy in your own archive is the only stable reference.</p>
<pre><code>hiring-closures, "Which companies are closing job postings fastest", {start} to {end}.
{url_of("closing-fastest.html")}
Data: {RAW}closures-72h.csv (CC0 1.0)</code></pre>
<p class="small muted">To resolve a slug to a company name, use the CC0 directory at
<a href="https://github.com/moonie0201/ats-directory">moonie0201/ats-directory</a>.</p>
"""
    return page(
        "closing-fastest.html",
        f"Companies closing job postings fastest, {start} to {end} — hiring-closures",
        f"Company careers boards ranked by job postings closed and by closure share, "
        f"{start} to {end}, recomputed daily from a CC0 file of company-day counts across "
        f"five ATS platforms. Formula stated; every number reproducible.",
        body,
    )


def month_grid(
    year: int,
    month: int,
    days: dict[str, dict],
    first_recorded: date,
    latest: date,
    linked: set[str],
) -> str:
    first = date(year, month, 1)
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cells = [f'<div class="wd">{w}</div>' for w in weekdays]
    cells += ['<div class="off"></div>'] * first.weekday()
    d = first
    while d.month == month:
        iso = d.isoformat()
        if iso in days:
            s = days[iso]
            tag, attrs = ("a", f' href="#d-{iso}"') if iso in linked else ("div", "")
            cells.append(
                f'<{tag} class="day"{attrs}><b>{d.day}</b>'
                f"<span>+{n(s['opened'])} / −{n(s['closed'])}</span>"
                f"<span>net {signed(s['net'])}</span>"
                f'<span class="muted">{n(s["boards"])} boards</span></{tag}>'
            )
        else:
            if d < COLLECTION_START:
                state = "before collection began"
            elif d < first_recorded:
                state = "before this record"
            elif d > latest:
                state = "not yet"
            else:
                state = "not in this record"
            cells.append(f'<div class="none"><b>{d.day}</b><span>{state}</span></div>')
        d += timedelta(days=1)
    return (
        f'<h2>{first.strftime("%B %Y")}</h2>\n<div class="cal">{"".join(cells)}</div>\n'
    )


def day_section(s: dict, in_file: bool) -> str:
    cols = [
        ("Company", "", lambda r: f"<code>{esc(r['company'])}</code>"),
        ("Provider", "", lambda r: esc(r["provider"])),
        ("Open", "n", lambda r: n(r["open"])),
        ("Added", "n", lambda r: n(r["added"])),
        ("Removed", "n", lambda r: n(r["removed"])),
    ]
    base = (
        f" ({n(s['baseline'])} first-day baselines, excluded from the flows)"
        if s["baseline"]
        else ""
    )
    source = (
        "In the current free file."
        if in_file
        else "Outside the rolling 72-hour file; retained from the build of that day."
    )
    return f"""<section id="d-{s["d"]}">
<h3>{s["d"]}</h3>
<p><strong>{n(s["opened"])}</strong> opened, <strong>{n(s["closed"])}</strong> closed,
net <strong>{signed(s["net"])}</strong>, {n(s["open"])} open across {n(s["boards"])} boards
measured{base}. <span class="muted">{source}</span></p>
<div class="two">
<div><h4>Top closers</h4>{table(s["closers"], cols) if s["closers"] else "<p class='muted'>none</p>"}</div>
<div><h4>Top openers</h4>{table(s["openers"], cols) if s["openers"] else "<p class='muted'>none</p>"}</div>
</div>
</section>
"""


def calendar_page(history: list[dict], file_days: set[str]) -> str:
    days = {e["d"]: e for e in history}
    first_recorded = date.fromisoformat(history[0]["d"])
    latest = date.fromisoformat(history[-1]["d"])
    months = sorted({(int(d[:4]), int(d[5:7])) for d in days})
    detailed = history[-DAY_SECTIONS:]
    linked = {e["d"] for e in detailed}
    grids = "".join(
        month_grid(y, m, days, first_recorded, latest, linked) for y, m in months
    )
    sections = "".join(day_section(e, e["d"] in file_days) for e in reversed(detailed))
    body = f"""<h1>Every day on record</h1>
<p class="lede">Postings opened, closed and net across the five-provider free file, one cell
per day, from the first day of this record ({history[0]["d"]}; collection began
{COLLECTION_START}) to the latest measured day ({latest}). Cells for the last {DAY_SECTIONS}
days link to that day's top {TOP_DAY} closers and openers.</p>
<p>The free file only ever holds the last 72 hours, so this page keeps its own record,
<a href="daily.jsonl"><code>daily.jsonl</code></a>. Days still inside the 72-hour file are
recomputed from it on every rebuild; days that have rolled out keep the totals they were
built with, minus any company that has since asked to be removed from the top lists. Today
it holds {len(history)} day{"s" if len(history) != 1 else ""}; it fills in one cell per day.
A day with no cell never passed through a build — it was not collected, or the daily rebuild
did not run; it is never a zero. Days between the start of collection and the first day of this record (this page
began with the file as it stood on {history[0]["d"]}; {COLLECTION_START} covered one shard of
four, 385 boards) exist in the paid archive but never passed through a build. Opened, closed
and net sum only boards with a previous-day snapshot; a board's first day is a baseline and
counts toward boards measured only.</p>
{grids}
<h2 id="days">Day by day</h2>
{sections}"""
    return page(
        "calendar.html",
        f"Job postings opened and closed by day, {history[0]['d']} to {history[-1]['d']} — hiring-closures",
        "A calendar of how many job postings company careers boards opened and closed each "
        "day across five ATS platforms, with the top closers and openers per day. Recomputed "
        "daily from a CC0 file of company-day counts.",
        body,
    )


def sitemap(lastmod: str) -> str:
    urls = "".join(
        f"  <url><loc>{url_of(f)}</loc><lastmod>{lastmod}</lastmod></url>\n"
        for f, _ in PAGES
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n"
    )


# --- main --------------------------------------------------------------------------


def build(blocklist: Path | None = None) -> None:
    blocked = read_blocklist(blocklist)
    rows = [r for r in load() if key(r) not in blocked]
    days = sorted({r["d"] for r in rows})
    history = merge_history(rows, blocked)
    latest = [e for e in history if e["boards"] > e["baseline"]][-1]

    DOCS.mkdir(exist_ok=True)
    out = {
        "index.html": index_page(latest, days),
        "closing-fastest.html": closing_page(window(rows), days),
        "calendar.html": calendar_page(history, set(days)),
        "daily.jsonl": "".join(json.dumps(e, sort_keys=True) + "\n" for e in history),
        "sitemap.xml": sitemap(history[-1]["d"]),
        "robots.txt": f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n",
        "style.css": (SITE / "style.css").read_text(encoding="utf-8"),
        ".nojekyll": "",
    }
    for name, text in out.items():
        (DOCS / name).write_text(text, encoding="utf-8", newline="\n")
    print(
        f"docs/: {len(out)} files, {len(rows)} rows, {days[0]}..{days[-1]}, history {len(history)} days"
    )


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--blocklist", type=Path, help="provider:slug per line; dropped everywhere"
    )
    build(ap.parse_args(argv).blocklist)


if __name__ == "__main__":
    main()
