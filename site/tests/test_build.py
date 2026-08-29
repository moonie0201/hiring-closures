"""python -m pytest site/tests — the generator's maths, on hand-made rows and the real file."""

import build  # conftest.py puts site/ on sys.path
import pytest


def row(d, provider, company, open_, added, removed):
    return {
        "d": d,
        "provider": provider,
        "company": company,
        "open": open_,
        "added": added,
        "removed": removed,
    }


ROWS = sorted(
    [
        # acme: seen on all three days; day 1 flows come from outside the window
        row("2026-08-27", "lever", "acme", 100, 7, 9),
        row("2026-08-28", "lever", "acme", 95, 5, 10),
        row("2026-08-29", "lever", "acme", 90, 5, 10),
        # beta: first day is a baseline (added empty), removed 0
        row("2026-08-27", "ashby", "beta", 50, None, 0),
        row("2026-08-28", "ashby", "beta", 48, 0, 2),
        row("2026-08-29", "ashby", "beta", 60, 12, 0),
        # gamma: same closed and share as delta -> provider/company tie order
        row("2026-08-27", "ashby", "gamma", 20, None, 0),
        row("2026-08-28", "ashby", "gamma", 16, 0, 4),
        row("2026-08-27", "greenhouse", "delta", 20, None, 0),
        row("2026-08-28", "greenhouse", "delta", 16, 0, 4),
        # tiny: below the floor, must never be ranked
        row("2026-08-27", "lever", "tiny", 3, None, 0),
        row("2026-08-28", "lever", "tiny", 0, 0, 3),
        # once: measured on one day only, no flows to rank
        row("2026-08-29", "rippling", "once", 500, None, 0),
    ],
    key=lambda r: (r["d"], r["provider"], r["company"]),
)


def test_baseline_rows_count_as_boards_but_never_as_flows():
    s = build.day_summary(ROWS, "2026-08-27")
    assert s["boards"] == 5 and s["baseline"] == 4
    assert (s["opened"], s["closed"], s["net"]) == (7, 9, -2)  # acme only
    assert s["open"] == 100 + 50 + 20 + 20 + 3
    assert [c["company"] for c in s["closers"]] == ["acme"]
    s29 = build.day_summary(ROWS, "2026-08-29")
    assert s29["boards"] == 3 and s29["baseline"] == 1  # `once` is a baseline
    assert (s29["opened"], s29["closed"], s29["net"]) == (17, 10, 7)
    assert [c["company"] for c in s29["openers"]] == ["beta", "acme"]


def test_window_ignores_first_day_flows_and_uses_the_stated_formula():
    w = {c["company"]: c for c in build.window(ROWS)}
    acme = w["acme"]
    assert (acme["open_start"], acme["added"], acme["closed"]) == (100, 10, 20)
    assert acme["share"] == pytest.approx(20 / (100 + 10))
    assert acme["open_end"] == acme["open_start"] + acme["added"] - acme["closed"]
    beta = w["beta"]
    assert (beta["added"], beta["closed"], beta["net"]) == (12, 2, 10)
    assert beta["share"] == pytest.approx(2 / 62)
    assert w["once"]["days"] == 1 and w["once"]["share"] == 0.0


def test_rank_floor_and_tie_order():
    w = build.window(ROWS)
    closed = [(c["provider"], c["company"]) for c in build.rank(w, "closed")]
    assert closed == [
        ("lever", "acme"),
        ("ashby", "gamma"),
        ("greenhouse", "delta"),
        ("ashby", "beta"),
    ]
    share = [c["company"] for c in build.rank(w, "share")]
    assert share == ["gamma", "delta", "acme", "beta"]  # 20% 20% 18.2% 3.2%
    net = [c["company"] for c in build.rank(w, "net")]
    assert net == ["beta"]  # only positive net is growth
    assert build.rank(w, "closed", limit=2) == build.rank(w, "closed")[:2]


def test_top_of_day_is_deterministic_and_drops_zeroes():
    flow = build.measured([r for r in ROWS if r["d"] == "2026-08-28"])
    assert [c["company"] for c in build.top(flow, "removed")] == [
        "acme",
        "gamma",
        "delta",
        "tiny",
        "beta",
    ]
    assert [c["company"] for c in build.top(flow, "added")] == ["acme"]
    assert set(build.top(flow, "removed")[0]) == set(build.COLUMNS)


@pytest.mark.skipif(not build.CSV.exists(), reason="sample file not present")
def test_real_file_stock_flow_identity_holds_for_every_company():
    rows = build.load()
    for c in build.window(rows):
        assert c["open_end"] == c["open_start"] + c["added"] - c["closed"], c
    for d in sorted({r["d"] for r in rows}):
        s = build.day_summary(rows, d)
        assert s["net"] == s["opened"] - s["closed"]
        assert s["boards"] >= s["baseline"]
        assert all(c["removed"] > 0 for c in s["closers"])


def test_closing_page_names_boards_whose_stock_flow_chain_breaks():
    # acme's 2026-08-28 row dropped (a board that went to zero is not published), so its
    # day-29 flows describe a change from a day outside the file: 100 + 5 - 10 != 90
    rows = [r for r in ROWS if not (r["company"] == "acme" and r["d"] == "2026-08-28")]
    days = ["2026-08-27", "2026-08-29"]
    page = build.closing_page(build.window(rows), days)
    assert (
        "holds for every row in this build except <code>lever:acme</code> (a day"
        in page
    )
    assert "holds for every row in this build. Only" in build.closing_page(
        build.window(ROWS), days
    )


def test_calendar_links_only_days_that_have_a_section(monkeypatch):
    monkeypatch.setattr(build, "DAY_SECTIONS", 1)
    history = [
        build.day_summary(ROWS, d) for d in ("2026-08-27", "2026-08-28", "2026-08-29")
    ]
    page = build.calendar_page(history, {"2026-08-29"})
    assert page.count('<section id="d-') == 1
    assert 'href="#d-2026-08-29"' in page and 'href="#d-2026-08-28"' not in page
    assert '<div class="day"><b>28</b>' in page
    assert "<span>not in this record</span>" not in page
    assert "first day of this record (2026-08-27; collection began" in page
