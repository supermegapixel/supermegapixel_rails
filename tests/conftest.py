from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from trustbuilder.api.app import create_app
from trustbuilder.config import Environment, Settings
from trustbuilder.keys import hash_key

# A throwaway key that exists only in this test suite.
TEST_KEY = "tb_test_suite-only-key"


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "env": Environment.TEST,
        "api_key_sha256": frozenset({hash_key(TEST_KEY)}),
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(make_settings())) as test_client:
        yield test_client


@pytest.fixture
def auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {TEST_KEY}"}
