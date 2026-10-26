"""Controlled vocabularies (PLAN.md §4). Codes come from the Build Plan's data model."""

from enum import StrEnum


class DataStatus(StrEnum):
    """Whether a response comes from fixtures or from real verification."""

    FIXTURE = "fixture"
    LIVE = "live"


class ClaimType(StrEnum):
    STATISTIC = "statistic"
    QUOTE = "quote"
    HISTORICAL_EVENT = "historical_event"
    SCIENTIFIC = "scientific"
    LEGAL_REGULATORY = "legal_regulatory"
    ATTRIBUTION_OF_ACTION = "attribution_of_action"
    CAUSAL = "causal"
    COMPARATIVE = "comparative"
    PREDICTION = "prediction"
    OPINION = "opinion"
    DEFINITION = "definition"
    OTHER = "other"


class Checkability(StrEnum):
    FACTUAL = "factual"
    OPINION = "opinion"
    PREDICTION = "prediction"
    MIXED = "mixed"


class VerdictStage(StrEnum):
    PROVISIONAL = "provisional"
    DEEP = "deep"
    RECHECK = "recheck"
    MANUAL_REVIEW = "manual_review"


class VerdictLabel(StrEnum):
    SUPPORTED = "supported"
    MOSTLY_SUPPORTED = "mostly_supported"
    MIXED = "mixed"
    MOSTLY_UNSUPPORTED = "mostly_unsupported"
    CONTRADICTED = "contradicted"
    UNVERIFIABLE = "unverifiable"
    MISLEADING_CONTEXT = "misleading_context"
    OUTDATED = "outdated"


class EvidenceStrength(StrEnum):
    THIN = "thin"
    MODERATE = "moderate"
    SOLID = "solid"


class SourceTier(StrEnum):
    PRIMARY_OFFICIAL = "primary_official"
    PRIMARY_RECORD = "primary_record"
    PEER_REVIEWED = "peer_reviewed"
    SYSTEMATIC_REVIEW = "systematic_review"
    REPUTABLE_SECONDARY = "reputable_secondary"
    ENCYCLOPEDIC = "encyclopedic"
    ADVOCACY = "advocacy"
    UNKNOWN = "unknown"


class Stance(StrEnum):
    SUPPORTS = "supports"
    PARTIALLY_SUPPORTS = "partially_supports"
    CONTRADICTS = "contradicts"
    CONTEXT_ONLY = "context_only"
    IRRELEVANT = "irrelevant"


class IndexStatus(StrEnum):
    SCORED = "scored"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ExposureBasis(StrEnum):
    """Where an outlet index's views/impressions denominator came from."""

    REPORTED = "reported"
    PANEL = "panel"
    ESTIMATED = "estimated"
    FIXTURE = "fixture"
