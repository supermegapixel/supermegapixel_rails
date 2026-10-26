"""Invariants every store's records must keep (store/models.py)."""

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from trustbuilder.store.models import ClaimRecord, OutletIndexSnapshot, VerdictVersion

RECEIPT: dict[str, Any] = {
    "source_name": "[FIXTURE] Source",
    "source_tier": "primary_official",
    "url": "https://source.example/x",
    "quote": "[FIXTURE] quote",
    "stance": "supports",
    "retrieved_at": "2026-10-01T00:00:00Z",
}


def verdict(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "version": 1,
        "stage": "deep",
        "created_at": "2026-10-01T01:00:00Z",
        "label": "supported",
        "score": 80,
        "confidence": 0.7,
        "evidence_strength": "moderate",
        "receipts": [RECEIPT],
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"score": None}, "no score exactly when"),
        ({"label": "unverifiable"}, "no score exactly when"),
        ({"confidence": None}, "confidence exactly when"),
        ({"receipts": []}, "at least one receipt"),
        ({"score": 101}, "less than or equal to 100"),
        ({"created_at": "2026-10-01T01:00:00"}, "timezone"),
    ],
)
def test_invalid_verdicts_are_rejected(overrides: dict[str, Any], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        VerdictVersion.model_validate(verdict(**overrides))


def test_unverifiable_verdict_without_score_or_receipts_is_valid() -> None:
    VerdictVersion.model_validate(
        verdict(label="unverifiable", score=None, confidence=None, receipts=[])
    )


def claim(*versions: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "clm_fixture_x",
        "text": "[FIXTURE] x",
        "type": "statistic",
        "checkability": "factual",
        "verdict_versions": list(versions),
    }


def test_verdict_versions_must_be_sequential() -> None:
    with pytest.raises(ValidationError, match="numbered 1, 2, 3"):
        ClaimRecord.model_validate(claim(verdict(version=1), verdict(version=3)))


def test_verdict_versions_must_be_chronological() -> None:
    with pytest.raises(ValidationError, match="chronological"):
        ClaimRecord.model_validate(
            claim(verdict(), verdict(version=2, created_at="2026-09-01T00:00:00Z"))
        )


def test_claim_record_exposes_original_and_current() -> None:
    record = ClaimRecord.model_validate(
        claim(verdict(), verdict(version=2, created_at="2026-10-02T00:00:00Z", score=60))
    )

    assert record.original.version == 1
    assert record.current.version == 2
    assert record.current.created_at == datetime(2026, 10, 2, tzinfo=UTC)


def snapshot(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "computed_at": "2026-10-19T06:00:00Z",
        "window": {"start": "2026-07-21", "end": "2026-10-18"},
        "status": "scored",
        "index": 60,
        "interval": {"low": 55, "high": 65, "level": 0.95},
        "minimum_claims_checked": 3,
        "inputs": {
            "articles_scored": 5,
            "claims_checked": 20,
            "claims_flagged": 2,
            "exposure": {"total": 1000, "basis": "fixture"},
            "third_party_mentions": 0,
        },
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"index": None}, "present exactly when status is 'scored'"),
        ({"status": "insufficient_evidence"}, "present exactly when status is 'scored'"),
        ({"index": 70}, "inside its interval"),
        ({"minimum_claims_checked": 50}, "at least minimum_claims_checked"),
        ({"window": {"start": "2026-10-18", "end": "2026-07-21"}}, "start on or before"),
    ],
)
def test_invalid_snapshots_are_rejected(overrides: dict[str, Any], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        OutletIndexSnapshot.model_validate(snapshot(**overrides))
