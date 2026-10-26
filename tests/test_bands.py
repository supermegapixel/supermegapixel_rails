import pytest

from trustbuilder.domain.bands import Band, band_for


@pytest.mark.parametrize(
    ("score", "band"),
    [
        (100, Band.VERIFIED),
        (75, Band.VERIFIED),
        (74, Band.LEANING_VERIFIED),
        (60, Band.LEANING_VERIFIED),
        (59, Band.MIXED),
        (40, Band.MIXED),
        (39, Band.LEANING_FALTERING),
        (25, Band.LEANING_FALTERING),
        (24, Band.FALTERING),
        (0, Band.FALTERING),
        (None, Band.INSUFFICIENT_EVIDENCE),
    ],
)
def test_brand_book_thresholds(score: int | None, band: Band) -> None:
    assert band_for(score) is band


@pytest.mark.parametrize("score", [-1, 101])
def test_out_of_range_scores_are_rejected(score: int) -> None:
    with pytest.raises(ValueError, match="between 0 and 100"):
        band_for(score)
