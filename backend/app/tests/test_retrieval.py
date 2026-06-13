"""Tests for retrieval service re-ranking logic."""
import pytest
from datetime import datetime, timedelta
from ..services.retrieval import _rerank


def make_candidate(source_type="commit", semantic=0.5, keyword=0.3, graph=0.0, date=None):
    return {
        "source_type": source_type,
        "source_id": f"id-{source_type}-{semantic}",
        "title": "test",
        "snippet": "retry payment idempotency key",
        "semantic_score": semantic,
        "keyword_score": keyword,
        "graph_score": graph,
        "date": date or datetime.utcnow() - timedelta(days=30),
    }


def test_rerank_pr_beats_commit_same_score():
    candidates = [
        make_candidate("commit", semantic=0.8),
        make_candidate("pull_request", semantic=0.8),
    ]
    ranked = _rerank(candidates, "retry logic", None)
    assert ranked[0]["source_type"] == "pull_request"


def test_rerank_semantic_dominant():
    candidates = [
        make_candidate("commit", semantic=0.9, keyword=0.1),
        make_candidate("pull_request", semantic=0.3, keyword=0.9),
    ]
    ranked = _rerank(candidates, "generic question", None)
    # High semantic commit should win over low-semantic PR when semantic=0.9
    assert ranked[0]["semantic_score"] == 0.9


def test_rerank_recency_bonus():
    recent = make_candidate("commit", semantic=0.5, date=datetime.utcnow() - timedelta(days=10))
    old = make_candidate("commit", semantic=0.5, date=datetime.utcnow() - timedelta(days=1800))
    ranked = _rerank([old, recent], "question", None)
    assert ranked[0]["date"] > ranked[1]["date"]


def test_rerank_keyword_boost_from_snippet():
    candidates = [
        make_candidate("issue", semantic=0.4),
    ]
    ranked = _rerank(candidates, "retry payment idempotency", None)
    # snippet contains "retry payment idempotency" so keyword score should be boosted
    assert ranked[0]["final_score"] > 0.10


def test_rerank_empty():
    assert _rerank([], "question", None) == []


def test_rerank_all_types():
    candidates = [
        make_candidate("code"),
        make_candidate("commit"),
        make_candidate("comment"),
        make_candidate("issue", semantic=0.7),
        make_candidate("pull_request", semantic=0.7),
        make_candidate("doc"),
    ]
    ranked = _rerank(candidates, "payment retry", None)
    assert len(ranked) == 6
    # All have final_score
    for c in ranked:
        assert "final_score" in c
        assert 0 <= c["final_score"] <= 1.5
