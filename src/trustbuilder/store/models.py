"""Records a ScoreStore returns. They mirror the append-only tables in PLAN.md §4.

Validators enforce the invariants every store must keep, whatever the backend:
a verdict has a score exactly when it isn't "unverifiable", a scored verdict has
receipts, and histories are in order.
"""

from datetime import date
from itertools import pairwise
from typing import Annotated, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, model_validator

from trustbuilder.domain.vocabulary import (
    Checkability,
    ClaimType,
    EvidenceStrength,
    ExposureBasis,
    IndexStatus,
    SourceTier,
    Stance,
    VerdictLabel,
    VerdictStage,
)

Score = Annotated[int, Field(ge=0, le=100)]
Fraction = Annotated[float, Field(ge=0, le=1)]
Count = Annotated[int, Field(ge=0)]


class Record(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Receipt(Record):
    """One piece of evidence a verdict relied on."""

    source_name: str
    source_tier: SourceTier
    url: HttpUrl
    archive_url: HttpUrl | None = None
    quote: str
    stance: Stance
    retrieved_at: AwareDatetime


class VerdictVersion(Record):
    version: int = Field(ge=1)
    stage: VerdictStage
    created_at: AwareDatetime
    label: VerdictLabel
    score: Score | None
    confidence: Fraction | None
    evidence_strength: EvidenceStrength
    receipts: tuple[Receipt, ...] = ()

    @model_validator(mode="after")
    def _check_scoring(self) -> Self:
        unscored = self.score is None
        if unscored != (self.label is VerdictLabel.UNVERIFIABLE):
            raise ValueError("a verdict has no score exactly when its label is 'unverifiable'")
        if unscored != (self.confidence is None):
            raise ValueError("a verdict has a confidence exactly when it has a score")
        if not unscored and not self.receipts:
            raise ValueError("a scored verdict needs at least one receipt")
        return self


class ClaimRecord(Record):
    """A canonical claim and its full verdict history, oldest first."""

    id: str
    text: str
    type: ClaimType
    checkability: Checkability
    verdict_versions: tuple[VerdictVersion, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_history(self) -> Self:
        numbers = [v.version for v in self.verdict_versions]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError("verdict versions must be numbered 1, 2, 3, ... in order")
        times = [v.created_at for v in self.verdict_versions]
        if times != sorted(times):
            raise ValueError("verdict versions must be in chronological order")
        return self

    @property
    def original(self) -> VerdictVersion:
        return self.verdict_versions[0]

    @property
    def current(self) -> VerdictVersion:
        return self.verdict_versions[-1]


class ScoringWindow(Record):
    start: date
    end: date

    @model_validator(mode="after")
    def _check_order(self) -> Self:
        if self.start > self.end:
            raise ValueError("a scoring window must start on or before its end")
        return self


class Exposure(Record):
    """Total views/impressions behind an index, and where the number came from."""

    total: Count
    basis: ExposureBasis


class IndexInputs(Record):
    articles_scored: Count
    claims_checked: Count
    claims_flagged: Count
    exposure: Exposure
    third_party_mentions: Count

    @model_validator(mode="after")
    def _check_counts(self) -> Self:
        if self.claims_flagged > self.claims_checked:
            raise ValueError("claims_flagged can't exceed claims_checked")
        return self


class Interval(Record):
    low: Score
    high: Score
    level: Fraction

    @model_validator(mode="after")
    def _check_order(self) -> Self:
        if self.low > self.high:
            raise ValueError("an interval's low bound can't exceed its high bound")
        return self


class OutletIndexSnapshot(Record):
    computed_at: AwareDatetime
    window: ScoringWindow
    status: IndexStatus
    index: Score | None
    interval: Interval | None
    minimum_claims_checked: int = Field(ge=1)
    inputs: IndexInputs

    @model_validator(mode="after")
    def _check_status(self) -> Self:
        scored = self.status is IndexStatus.SCORED
        if scored != (self.index is not None) or scored != (self.interval is not None):
            raise ValueError("an index and interval are present exactly when status is 'scored'")
        if self.index is not None and self.interval is not None:
            if not self.interval.low <= self.index <= self.interval.high:
                raise ValueError("the index must lie inside its interval")
            if self.inputs.claims_checked < self.minimum_claims_checked:
                raise ValueError("a scored index needs at least minimum_claims_checked claims")
        return self


class OutletRecord(Record):
    """An outlet and its trust-index history, oldest first."""

    id: str
    name: str
    domains: tuple[str, ...] = Field(min_length=1)
    index_snapshots: tuple[OutletIndexSnapshot, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_history(self) -> Self:
        times = [s.computed_at for s in self.index_snapshots]
        if any(earlier >= later for earlier, later in pairwise(times)):
            raise ValueError("index snapshots must be in strictly increasing computed_at order")
        return self

    @property
    def current(self) -> OutletIndexSnapshot:
        return self.index_snapshots[-1]

    @property
    def previous(self) -> OutletIndexSnapshot | None:
        return self.index_snapshots[-2] if len(self.index_snapshots) > 1 else None
