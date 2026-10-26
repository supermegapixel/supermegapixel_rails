import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_settings
from trustbuilder.api.app import create_app

PROTECTED = ["/v1/claims/clm_fixture_0001/score", "/v1/outlets/out_fixture_01/trust-index"]


@pytest.mark.parametrize("path", PROTECTED)
def test_missing_key_is_401(client: TestClient, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "unauthorized"


@pytest.mark.parametrize(
    "header",
    ["Bearer tb_test_wrong", "Basic dGJfdGVzdDp4", "tb_test_suite-only-key"],
    ids=["wrong key", "wrong scheme", "no scheme"],
)
def test_bad_credentials_are_401(client: TestClient, header: str) -> None:
    response = client.get(PROTECTED[0], headers={"Authorization": header})

    assert response.status_code == 401


def test_valid_key_is_accepted(client: TestClient, auth: dict[str, str]) -> None:
    assert client.get(PROTECTED[0], headers=auth).status_code == 200


def test_health_needs_no_key(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_no_configured_keys_rejects_everyone(auth: dict[str, str]) -> None:
    with TestClient(create_app(make_settings(api_key_sha256=frozenset()))) as client:
        assert client.get(PROTECTED[0], headers=auth).status_code == 401
