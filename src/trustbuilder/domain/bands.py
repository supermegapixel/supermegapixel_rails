"""Score bands from the Brand Book (section 3B, score glyph).

The thresholds are the Brand Book's proposed starting values. They have not been
calibrated against real score distributions yet.
"""

from enum import StrEnum


class Band(StrEnum):
    VERIFIED = "verified"
    LEANING_VERIFIED = "leaning_verified"
    MIXED = "mixed"
    LEANING_FALTERING = "leaning_faltering"
    FALTERING = "faltering"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


# Lowest score in each band, highest band first. Anything below 25 is faltering.
_FLOORS: tuple[tuple[int, Band], ...] = (
    (75, Band.VERIFIED),
    (60, Band.LEANING_VERIFIED),
    (40, Band.MIXED),
    (25, Band.LEANING_FALTERING),
)


def band_for(score: int | None) -> Band:
    """Map a 0-100 score to its band. A missing score means insufficient evidence."""
    if score is None:
        return Band.INSUFFICIENT_EVIDENCE
    if not 0 <= score <= 100:
        raise ValueError(f"score must be between 0 and 100, got {score}")
    for floor, band in _FLOORS:
        if score >= floor:
            return band
    return Band.FALTERING
