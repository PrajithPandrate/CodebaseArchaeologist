from ..services.github_metadata import extract_issue_refs, extract_all_issue_mentions, parse_datetime


def test_extract_fixes_pattern():
    text = "Fixes #89 and resolves #124"
    refs = extract_issue_refs(text)
    assert 89 in refs
    assert 124 in refs


def test_extract_closes_pattern():
    text = "closes #42"
    refs = extract_issue_refs(text)
    assert 42 in refs


def test_no_refs():
    text = "Refactor payment service"
    refs = extract_issue_refs(text)
    assert refs == []


def test_extract_all_mentions():
    text = "Related to #89, see also #100 and #200"
    mentions = extract_all_issue_mentions(text)
    assert 89 in mentions
    assert 100 in mentions
    assert 200 in mentions


def test_parse_datetime_iso():
    dt = parse_datetime("2024-01-15T10:30:00Z")
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 15


def test_parse_datetime_none():
    assert parse_datetime(None) is None
    assert parse_datetime("") is None
