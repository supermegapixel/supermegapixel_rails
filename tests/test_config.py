import hashlib

import pytest
from pydantic import ValidationError

from trustbuilder.config import Environment, Settings
from trustbuilder.keys import LIVE_PREFIX, TEST_PREFIX, generate_key, hash_key, main

DIGEST_A = hashlib.sha256(b"a").hexdigest()
DIGEST_B = hashlib.sha256(b"b").hexdigest()


def test_defaults_are_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("TRUSTBUILDER_ENV", "TRUSTBUILDER_API_KEY_SHA256", "TRUSTBUILDER_STORE"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.env is Environment.DEVELOPMENT
    assert settings.api_key_sha256 == frozenset()
    assert settings.store == "fixture"


def test_reads_comma_separated_digests_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TRUSTBUILDER_API_KEY_SHA256", f" {DIGEST_A.upper()} ,{DIGEST_B},, ")

    assert Settings(_env_file=None).api_key_sha256 == {DIGEST_A, DIGEST_B}


def test_a_raw_key_is_rejected_without_echoing_it(monkeypatch: pytest.MonkeyPatch) -> None:
    raw_key = generate_key()
    monkeypatch.setenv("TRUSTBUILDER_API_KEY_SHA256", raw_key)

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    assert "not the key itself" in str(error.value)
    assert raw_key not in str(error.value)


def test_unknown_store_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUSTBUILDER_STORE", "postgres")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_generated_keys_have_the_right_prefix_and_entropy() -> None:
    assert generate_key().startswith(TEST_PREFIX)
    assert generate_key(live=True).startswith(LIVE_PREFIX)
    assert generate_key() != generate_key()
    assert len(generate_key()) > len(TEST_PREFIX) + 40


def test_key_cli_prints_a_key_and_its_digest(capsys: pytest.CaptureFixture[str]) -> None:
    main([])
    lines = capsys.readouterr().out.splitlines()

    key = lines[0].removeprefix("key:").strip()
    digest = lines[1].removeprefix("sha256:").strip()
    assert key.startswith(TEST_PREFIX)
    assert digest == hash_key(key)
