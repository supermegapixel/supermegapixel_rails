from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient

from trustbuilder.api.schemas import HISTORY_POINTS, OutletTrustIndex
from trustbuilder.domain.bands import band_for
from trustbuilder.domain.vocabulary import ExposureBasis, IndexStatus
from trustbuilder.store.models import (
    Exposure,
    IndexInputs,
    Interval,
    OutletIndexSnapshot,
    OutletRecord,
    ScoringWindow,
)


def get_index(client: TestClient, auth: dict[str, str], outlet_id: str) -> dict[str, Any]:
    response = client.get(f"/v1/outlets/{outlet_id}/trust-index", headers=auth)
    assert response.status_code == 200, response.text
    data: dict[str, Any] = response.json()["data"]
    return data


def test_scored_outlet(client: TestClient, auth: dict[str, str]) -> None:
    data = get_index(client, auth, "out_fixture_01")
    current = data["current"]

    assert data["object"] == "outlet_trust_index"
    assert data["outlet"]["domains"] == ["outlet-a.example"]
    assert current["status"] == "scored"
    assert current["band"] == band_for(current["index"])
    assert current["interval"]["low"] <= current["index"] <= current["interval"]["high"]
    assert current["inputs"]["exposure"]["basis"] == "fixture"


def test_change_is_current_minus_previous(client: TestClient, auth: dict[str, str]) -> None:
    data = get_index(client, auth, "out_fixture_01")

    assert data["change"] == data["current"]["index"] - data["previous"]["index"]
    assert data["previous"]["computed_at"] < data["current"]["computed_at"]


def test_history_is_oldest_first_and_ends_at_current(
    client: TestClient, auth: dict[str, str]
) -> None:
    data = get_index(client, auth, "out_fixture_01")
    times = [point["computed_at"] for point in data["history"]]

    assert times == sorted(times)
    assert times[-1] == data["current"]["computed_at"]


def test_index_can_cross_a_band_boundary(client: TestClient, auth: dict[str, str]) -> None:
    data = get_index(client, auth, "out_fixture_03")

    assert band_for(data["previous"]["index"]) == "mixed"
    assert data["current"]["band"] == "leaning_faltering"
    assert data["change"] < 0


def test_too_few_claims_is_200_with_insufficient_evidence(
    client: TestClient, auth: dict[str, str]
) -> None:
    data = get_index(client, auth, "out_fixture_02")
    current = data["current"]

    assert current["status"] == "insufficient_evidence"
    assert current["index"] is None
    assert current["interval"] is None
    assert current["band"] == "insufficient_evidence"
    assert current["inputs"]["claims_checked"] < current["minimum_claims_checked"]
    assert data["previous"] is None
    assert data["change"] is None


def test_unknown_outlet_is_404(client: TestClient, auth: dict[str, str]) -> None:
    response = client.get("/v1/outlets/out_fixture_99/trust-index", headers=auth)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_history_is_capped_at_the_most_recent_points() -> None:
    start = datetime(2026, 1, 5, 6, tzinfo=UTC)
    snapshots = tuple(
        OutletIndexSnapshot(
            computed_at=start + timedelta(weeks=week),
            window=ScoringWindow(start=date(2025, 10, 1), end=date(2026, 1, 4)),
            status=IndexStatus.SCORED,
            index=50 + week,
            interval=Interval(low=40 + week, high=60 + week, level=0.95),
            minimum_claims_checked=3,
            inputs=IndexInputs(
                articles_scored=10,
                claims_checked=50,
                claims_flagged=5,
                exposure=Exposure(total=1000, basis=ExposureBasis.FIXTURE),
                third_party_mentions=0,
            ),
        )
        for week in range(HISTORY_POINTS + 3)
    )
    outlet = OutletRecord(
        id="out_fixture_cap",
        name="[FIXTURE] Cap",
        domains=("cap.example",),
        index_snapshots=snapshots,
    )

    history = OutletTrustIndex.from_record(outlet).history

    assert len(history) == HISTORY_POINTS
    assert history[-1].computed_at == snapshots[-1].computed_at
    assert history[0].computed_at == snapshots[3].computed_at
