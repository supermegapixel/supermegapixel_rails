from fastapi.testclient import TestClient

from tests.conftest import make_settings
from trustbuilder.api.app import create_app
from trustbuilder.domain.vocabulary import DataStatus
from trustbuilder.store.models import ClaimRecord, OutletRecord


class BrokenStore:
    data_status = DataStatus.FIXTURE
    methodology_version = "fixture"

    def get_claim(self, claim_id: str) -> ClaimRecord | None:
        raise RuntimeError("database is on fire")

    def get_outlet(self, outlet_id: str) -> OutletRecord | None:
        raise RuntimeError("database is on fire")


def test_unknown_endpoint_uses_the_error_envelope(client: TestClient) -> None:
    response = client.get("/v2/nothing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert "GET /v2/nothing" in response.json()["error"]["message"]


def test_wrong_method_uses_the_error_envelope(client: TestClient, auth: dict[str, str]) -> None:
    response = client.post("/v1/claims/clm_fixture_0001/score", headers=auth)

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_unexpected_errors_return_500_without_internals(auth: dict[str, str]) -> None:
    app = create_app(make_settings(), store=BrokenStore())
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/v1/claims/clm_fixture_0001/score", headers=auth)

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "internal_error"
    assert "on fire" not in error["message"]
    assert error["request_id"].startswith("req_")


def test_openapi_lists_both_endpoints(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/v1/claims/{claim_id}/score" in paths
    assert "/v1/outlets/{outlet_id}/trust-index" in paths
