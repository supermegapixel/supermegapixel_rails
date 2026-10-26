"""API key generation and hashing.

A key is shown once, when it is generated. The server only ever holds its SHA-256 digest.

Usage: python -m trustbuilder.keys [--live]
"""

import argparse
import hashlib
import secrets

LIVE_PREFIX = "tb_live_"
TEST_PREFIX = "tb_test_"


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_key(*, live: bool = False) -> str:
    return (LIVE_PREFIX if live else TEST_PREFIX) + secrets.token_urlsafe(32)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate a TrustBuilder API key and its SHA-256 digest."
    )
    parser.add_argument(
        "--live", action="store_true", help=f"use the {LIVE_PREFIX} prefix instead of {TEST_PREFIX}"
    )
    args = parser.parse_args(argv)
    key = generate_key(live=args.live)
    print(f"key:    {key}")
    print(f"sha256: {hash_key(key)}")
    print("Give the key to the client. Put only the sha256 in TRUSTBUILDER_API_KEY_SHA256.")


if __name__ == "__main__":
    main()
