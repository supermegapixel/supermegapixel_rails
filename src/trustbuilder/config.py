"""Settings, read from environment variables (prefix TRUSTBUILDER_) and an optional .env file."""

import re
from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_SHA256_HEX = re.compile(r"[0-9a-f]{64}")


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # hide_input_in_errors: a misconfigured key variable may hold a raw API key,
    # and validation errors must never echo it into logs.
    model_config = SettingsConfigDict(
        env_prefix="TRUSTBUILDER_",
        env_file=".env",
        extra="ignore",
        hide_input_in_errors=True,
    )

    env: Environment = Environment.DEVELOPMENT
    # SHA-256 hex digests of the accepted API keys. Comma-separated in the environment.
    api_key_sha256: Annotated[frozenset[str], NoDecode] = frozenset()
    # Only the fixture store exists until the Postgres store lands (PLAN.md §6, S0).
    store: Literal["fixture"] = "fixture"

    @field_validator("api_key_sha256", mode="before")
    @classmethod
    def _parse_digests(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.split(",")
        if not isinstance(value, list | tuple | set | frozenset):
            return value
        digests = frozenset(str(item).strip().lower() for item in value if str(item).strip())
        if not all(_SHA256_HEX.fullmatch(digest) for digest in digests):
            raise ValueError(
                "each entry must be the 64-character hex SHA-256 digest of an API key, "
                "not the key itself; generate one with: python -m trustbuilder.keys"
            )
        return digests


@lru_cache
def get_settings() -> Settings:
    return Settings()
