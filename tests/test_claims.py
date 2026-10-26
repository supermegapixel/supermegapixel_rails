from typing import Any

from fastapi.testclient import TestClient

from trustbuilder.domain.bands import band_for


def get_score(client: TestClient, auth: dict[str, str], claim_id: str) -> dict[str, Any]:
    response = client.get(f"/v1/claims/{claim_id}/score", headers=auth)
    assert response.status_code == 200, response.text
    data: dict[str, Any] = response.json()["data"]
    return data


def test_returns_original_and_current_verdicts(client: TestClient, auth: dict[str, str]) -> None:
    data = get_score(client, auth, "clm_fixture_0001")

    assert data["id"] == "clm_fixture_0001"
    assert data["object"] == "claim_score"
    assert data["claim"]["type"] == "statistic"
    assert data["versions_count"] == 2
    assert data["original"]["verdict_version"] == 1
    assert data["original"]["stage"] == "provisional"
    assert data["current"]["verdict_version"] == 2
    assert data["current"]["stage"] == "deep"
    assert data["current"]["label"] == "contradicted"


def test_scored_verdict_has_band_confidence_and_receipts(
    client: TestClient, auth: dict[str, str]
) -> None:
    current = get_score(client, auth, "clm_fixture_0001")["current"]

    assert current["band"] == band_for(current["score"])
    assert 0 <= current["confidence"] <= 1
    assert current["receipts"], "a scored verdict must carry its receipts"
    receipt = current["receipts"][0]
    assert set(receipt) == {
        "source_name",
        "source_tier",
        "url",
        "archive_url",
        "quote",
        "stance",
        "retrieved_at",
    }


def test_single_version_claim_reports_same_original_and_current(
    client: TestClient, auth: dict[str, str]
) -> None:
    data = get_score(client, auth, "clm_fixture_0002")

    assert data["versions_count"] == 1
    assert data["original"] == data["current"]


def test_recheck_that_changes_a_verdict_shows_both(
    client: TestClient, auth: dict[str, str]
) -> None:
    data = get_score(client, auth, "clm_fixture_0004")

    assert data["current"]["stage"] == "recheck"
    assert data["original"]["score"] != data["current"]["score"]


def test_unverifiable_claim_is_200_with_null_score(
    client: TestClient, auth: dict[str, str]
) -> None:
    current = get_score(client, auth, "clm_fixture_0003")["current"]

    assert current["label"] == "unverifiable"
    assert current["score"] is None
    assert current["confidence"] is None
    assert current["band"] == "insufficient_evidence"
    assert current["evidence_strength"] == "thin"


def test_unknown_claim_is_404(client: TestClient, auth: dict[str, str]) -> None:
    response = client.get("/v1/claims/clm_fixture_9999/score", headers=auth)

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert "clm_fixture_9999" in error["message"]
    assert error["request_id"] == response.headers["X-Request-ID"]


def test_wrong_id_prefix_explains_the_format(client: TestClient, auth: dict[str, str]) -> None:
    response = client.get("/v1/claims/out_fixture_01/score", headers=auth)

    assert response.status_code == 404
    assert "start with 'clm_'" in response.json()["error"]["message"]
