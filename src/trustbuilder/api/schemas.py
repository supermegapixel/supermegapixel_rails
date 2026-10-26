"""Response bodies (PLAN.md §5). Each data endpoint returns {"data": ..., "meta": ...}."""

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel

from trustbuilder.domain.bands import Band, band_for
from trustbuilder.domain.vocabulary import (
    Checkability,
    ClaimType,
    DataStatus,
    EvidenceStrength,
    IndexStatus,
    VerdictLabel,
    VerdictStage,
)
from trustbuilder.store.models import (
    ClaimRecord,
    IndexInputs,
    Interval,
    OutletIndexSnapshot,
    OutletRecord,
    Receipt,
    ScoringWindow,
    VerdictVersion,
)

# Points returned for a sparkline. The full series gets its own endpoint in Phase 2.
HISTORY_POINTS = 12


class Meta(BaseModel):
    data_status: DataStatus
    methodology_version: str
    generated_at: datetime
    request_id: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class Health(BaseModel):
    status: Literal["ok"] = "ok"
    version: str
    data_status: DataStatus


# Claims


class ClaimSummary(BaseModel):
    text: str
    type: ClaimType
    checkability: Checkability


class Verdict(BaseModel):
    verdict_version: int
    stage: VerdictStage
    checked_at: datetime
    label: VerdictLabel
    score: int | None
    band: Band
    confidence: float | None
    evidence_strength: EvidenceStrength
    receipts: list[Receipt]

    @classmethod
    def from_record(cls, verdict: VerdictVersion) -> Self:
        return cls(
            verdict_version=verdict.version,
            stage=verdict.stage,
            checked_at=verdict.created_at,
            label=verdict.label,
            score=verdict.score,
            band=band_for(verdict.score),
            confidence=verdict.confidence,
            evidence_strength=verdict.evidence_strength,
            receipts=list(verdict.receipts),
        )


class ClaimScore(BaseModel):
    id: str
    object: Literal["claim_score"] = "claim_score"
    claim: ClaimSummary
    current: Verdict
    original: Verdict
    versions_count: int

    @classmethod
    def from_record(cls, claim: ClaimRecord) -> Self:
        return cls(
            id=claim.id,
            claim=ClaimSummary(text=claim.text, type=claim.type, checkability=claim.checkability),
            current=Verdict.from_record(claim.current),
            original=Verdict.from_record(claim.original),
            versions_count=len(claim.verdict_versions),
        )


class ClaimScoreResponse(BaseModel):
    data: ClaimScore
    meta: Meta


# Outlets


class OutletSummary(BaseModel):
    name: str
    domains: list[str]


class TrustIndex(BaseModel):
    status: IndexStatus
    index: int | None
    band: Band
    interval: Interval | None
    window: ScoringWindow
    computed_at: datetime
    minimum_claims_checked: int
    inputs: IndexInputs

    @classmethod
    def from_record(cls, snapshot: OutletIndexSnapshot) -> Self:
        return cls(
            status=snapshot.status,
            index=snapshot.index,
            band=band_for(snapshot.index),
            interval=snapshot.interval,
            window=snapshot.window,
            computed_at=snapshot.computed_at,
            minimum_claims_checked=snapshot.minimum_claims_checked,
            inputs=snapshot.inputs,
        )


class IndexPoint(BaseModel):
    computed_at: datetime
    status: IndexStatus
    index: int | None

    @classmethod
    def from_record(cls, snapshot: OutletIndexSnapshot) -> Self:
        return cls(computed_at=snapshot.computed_at, status=snapshot.status, index=snapshot.index)


class OutletTrustIndex(BaseModel):
    id: str
    object: Literal["outlet_trust_index"] = "outlet_trust_index"
    outlet: OutletSummary
    current: TrustIndex
    previous: IndexPoint | None
    # current.index - previous.index; null unless both are scored.
    change: int | None
    # Oldest first, ending with the current snapshot.
    history: list[IndexPoint]

    @classmethod
    def from_record(cls, outlet: OutletRecord) -> Self:
        current, previous = outlet.current, outlet.previous
        change = None
        if previous is not None and current.index is not None and previous.index is not None:
            change = current.index - previous.index
        return cls(
            id=outlet.id,
            outlet=OutletSummary(name=outlet.name, domains=list(outlet.domains)),
            current=TrustIndex.from_record(current),
            previous=IndexPoint.from_record(previous) if previous is not None else None,
            change=change,
            history=[IndexPoint.from_record(s) for s in outlet.index_snapshots[-HISTORY_POINTS:]],
        )


class OutletTrustIndexResponse(BaseModel):
    data: OutletTrustIndex
    meta: Meta
