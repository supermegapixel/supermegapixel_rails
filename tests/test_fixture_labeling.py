"""Fixture data must never pass for real data (fixtures/README.md, PLAN.md §7)."""

from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient
from pydantic import HttpUrl

from tests.conftest import make_settings
from trustbuilder.api.app import create_app
from trustbuilder.config import Environment
from trustbuilder.store.fixture_store import (
    FIXTURE_MARK,
    FixtureError,
    FixtureStore,
    is_reserved_domain,
    labeling_problems,
    load_packaged_fixtures,
)
from trustbuilder.store.models import ClaimRecord, OutletRecord

CLAIMS, OUTLETS = load_packaged_fixtures()


def claim_by_id(claim_id: str) -> ClaimRecord:
    return next(claim for claim in CLAIMS if claim.id == claim_id)


def outlet_by_id(outlet_id: str) -> OutletRecord:
    return next(outlet for outlet in OUTLETS if outlet.id == outlet_id)


PATHS = [
    "/health",
    "/v1/claims/clm_fixture_0001/score",
    "/v1/outlets/out_fixture_01/trust-index",
    "/v1/claims/clm_fixture_9999/score",
    "/v1/no-such-endpoint",
]
DATA_PATHS = PATHS[1:3]


@pytest.mark.parametrize("path", PATHS)
def test_every_response_has_the_fixture_header(
    client: TestClient, auth: dict[str, str], path: str
) -> None:
    response = client.get(path, headers=auth)

    assert response.headers["X-TrustBuilder-Data"] == "fixture"
    assert response.headers["X-Request-ID"].startswith("req_")


def test_unauthenticated_responses_have_the_fixture_header(client: TestClient) -> None:
    assert client.get(DATA_PATHS[0]).headers["X-TrustBuilder-Data"] == "fixture"


@pytest.mark.parametrize("path", DATA_PATHS)
def test_data_responses_say_fixture_in_meta(
    client: TestClient, auth: dict[str, str], path: str
) -> None:
    response = client.get(path, headers=auth)
    meta = response.json()["meta"]

    assert meta["data_status"] == "fixture"
    assert meta["methodology_version"] == "fixture"
    assert meta["request_id"] == response.headers["X-Request-ID"]


def test_app_refuses_to_serve_fixtures_in_production() -> None:
    with pytest.raises(RuntimeError, match="fixture"):
        create_app(make_settings(env=Environment.PRODUCTION))


def test_shipped_fixtures_are_labeled() -> None:
    FixtureStore.from_package()  # raises FixtureError on any labeling problem

    assert CLAIMS
    assert OUTLETS
    assert labeling_problems(CLAIMS, OUTLETS) == []
    # Spelled out as well, so a bug in labeling_problems can't hide a real URL.
    for claim in CLAIMS:
        assert claim.text.startswith(FIXTURE_MARK)
        for verdict in claim.verdict_versions:
            for receipt in verdict.receipts:
                assert urlsplit(str(receipt.url)).hostname.endswith(".example")  # type: ignore[union-attr]
    for outlet in OUTLETS:
        assert outlet.name.startswith(FIXTURE_MARK)
        assert all(domain.endswith(".example") for domain in outlet.domains)


@pytest.mark.parametrize(
    ("host", "reserved"),
    [
        ("outlet-a.example", True),
        ("www.outlet-b.example", True),
        ("stats.invalid", True),
        ("example.org", True),
        ("news.example.com", True),
        ("example.com.attacker.net", False),
        ("notexample.com", False),
        ("nytimes.com", False),
    ],
)
def test_reserved_domains(host: str, reserved: bool) -> None:
    assert is_reserved_domain(host) is reserved


def test_store_rejects_an_unlabeled_claim() -> None:
    claim = claim_by_id("clm_fixture_0002")
    bad = claim.model_copy(update={"id": "clm_0002", "text": "Unlabeled claim"})

    with pytest.raises(FixtureError) as error:
        FixtureStore([bad], [])

    assert "must start with 'clm_fixture_'" in str(error.value)
    assert f"must start with {FIXTURE_MARK}" in str(error.value)


def test_store_rejects_a_receipt_on_a_real_domain() -> None:
    claim = claim_by_id("clm_fixture_0002")
    verdict = claim.verdict_versions[0]
    receipt = verdict.receipts[0].model_copy(update={"url": HttpUrl("https://not-reserved.com/x")})
    bad = claim.model_copy(
        update={"verdict_versions": (verdict.model_copy(update={"receipts": (receipt,)}),)}
    )

    with pytest.raises(FixtureError, match="not on a reserved domain"):
        FixtureStore([bad], [])


def test_store_rejects_an_outlet_on_a_real_domain() -> None:
    outlet = outlet_by_id("out_fixture_01").model_copy(update={"domains": ("not-reserved.com",)})

    with pytest.raises(FixtureError, match="not a reserved domain"):
        FixtureStore([], [outlet])


def test_store_rejects_duplicate_ids() -> None:
    claim = claim_by_id("clm_fixture_0002")

    with pytest.raises(FixtureError, match="duplicate claim id"):
        FixtureStore([claim, claim], [])
