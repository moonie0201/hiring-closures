import hashlib
import json

import build


def test_coverage_reports_only_observations_and_binds_source_bytes():
    rows = [
        {"d": "2026-10-01", "provider": "lever", "company": "example", "added": None},
        {"d": "2026-10-01", "provider": "lever", "company": "example", "added": 0},
        {"d": "2026-10-03", "provider": "ashby", "company": "example", "added": 0},
    ]
    result = build.coverage_manifest(rows, b"public csv bytes")
    assert result["source_sha256"] == hashlib.sha256(b"public csv bytes").hexdigest()
    assert result["first_day"] == "2026-10-01"
    assert result["latest_day"] == "2026-10-03"
    assert result["observed_days"] == 2
    assert result["board_count"] == 2
    assert result["expected_board_count"] is None
    assert result["coverage"] == [
        {"d": "2026-10-01", "rows": 2, "boards": 1, "baseline_rows": 1,
         "boards_by_provider": {"lever": 1}},
        {"d": "2026-10-03", "rows": 1, "boards": 1, "baseline_rows": 0,
         "boards_by_provider": {"ashby": 1}},
    ]
    assert "example" not in json.dumps(result)  # no individual board identifiers
    assert "status" not in result  # static artifact must not claim live freshness


def test_empty_coverage_has_unknown_dates():
    report = build.coverage_manifest([], b"")
    assert report["first_day"] is report["latest_day"] is None
    assert report["coverage"] == []


def test_inline_code_is_rendered_and_escaped():
    text = build.md_tables_to_html("`tracked_since` and `<script>`")
    assert "<code>tracked_since</code>" in text
    assert "<code>&lt;script&gt;</code>" in text
    assert "\\1" not in text


def test_export_separates_dated_cutoff_and_unavailable_checkout():
    text = build.export_page()
    assert "2026-09-09" in text
    assert "cutoff is independent" in text
    assert "Not on sale yet" in text
    assert "Buy the export" not in text
    assert "<code>tracked_since</code>" in text
