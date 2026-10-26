"""A ScoreStore backed by hand-written fixture files.

Fixture data is invented for API development. It is not real claims, sources,
outlets or scores. The store refuses any record that doesn't label itself as
fixture data; the rules are in fixtures/README.md.
"""

from collections.abc import Iterable
from importlib import resources
from urllib.parse import urlsplit

from pydantic import HttpUrl

from trustbuilder.domain.ids import CLAIM_PREFIX, OUTLET_PREFIX
from trustbuilder.domain.vocabulary import DataStatus, ExposureBasis
from trustbuilder.store.models import ClaimRecord, OutletRecord, Record

FIXTURE_MARK = "[FIXTURE]"
CLAIM_ID_PREFIX = f"{CLAIM_PREFIX}fixture_"
OUTLET_ID_PREFIX = f"{OUTLET_PREFIX}fixture_"

# Names reserved by RFC 2606 and RFC 6761, so a fixture can never point at a real site.
_RESERVED_TLDS = (".example", ".invalid", ".test", ".localhost")
_RESERVED_DOMAINS = ("example.com", "example.net", "example.org")


class FixtureError(ValueError):
    pass


class ClaimFixtures(Record):
    notice: str
    claims: tuple[ClaimRecord, ...]


class OutletFixtures(Record):
    notice: str
    outlets: tuple[OutletRecord, ...]


def is_reserved_domain(host: str) -> bool:
    host = host.lower().rstrip(".")
    return host.endswith(_RESERVED_TLDS) or any(
        host == domain or host.endswith(f".{domain}") for domain in _RESERVED_DOMAINS
    )


def labeling_problems(claims: Iterable[ClaimRecord], outlets: Iterable[OutletRecord]) -> list[str]:
    """Everything that would let fixture data pass for real data."""
    problems: list[str] = []

    def check_text(where: str, text: str) -> None:
        if not text.startswith(FIXTURE_MARK):
            problems.append(f"{where} must start with {FIXTURE_MARK}")

    def check_url(where: str, url: HttpUrl | None) -> None:
        if url is not None and not is_reserved_domain(urlsplit(str(url)).hostname or ""):
            problems.append(f"{where} {url} is not on a reserved domain (.example, .invalid, ...)")

    for claim in claims:
        if not claim.id.startswith(CLAIM_ID_PREFIX):
            problems.append(f"claim id {claim.id!r} must start with {CLAIM_ID_PREFIX!r}")
        check_text(f"claim {claim.id} text", claim.text)
        for verdict in claim.verdict_versions:
            for n, receipt in enumerate(verdict.receipts):
                where = f"claim {claim.id} v{verdict.version} receipt {n}"
                check_text(f"{where} source_name", receipt.source_name)
                check_text(f"{where} quote", receipt.quote)
                check_url(f"{where} url", receipt.url)
                check_url(f"{where} archive_url", receipt.archive_url)

    for outlet in outlets:
        if not outlet.id.startswith(OUTLET_ID_PREFIX):
            problems.append(f"outlet id {outlet.id!r} must start with {OUTLET_ID_PREFIX!r}")
        check_text(f"outlet {outlet.id} name", outlet.name)
        for domain in outlet.domains:
            if not is_reserved_domain(domain):
                problems.append(f"outlet {outlet.id} domain {domain!r} is not a reserved domain")
        for snapshot in outlet.index_snapshots:
            if snapshot.inputs.exposure.basis is not ExposureBasis.FIXTURE:
                problems.append(
                    f"outlet {outlet.id} snapshot {snapshot.computed_at} exposure basis "
                    f"must be 'fixture'"
                )

    return problems


class FixtureStore:
    data_status = DataStatus.FIXTURE
    methodology_version = "fixture"

    def __init__(self, claims: Iterable[ClaimRecord], outlets: Iterable[OutletRecord]) -> None:
        claims, outlets = tuple(claims), tuple(outlets)
        problems = labeling_problems(claims, outlets)
        if problems:
            listing = "\n- ".join(problems)
            raise FixtureError(f"fixture data isn't labeled as fixture data:\n- {listing}")
        self._claims = _by_id(claims, "claim")
        self._outlets = _by_id(outlets, "outlet")

    @classmethod
    def from_package(cls) -> "FixtureStore":
        return cls(*load_packaged_fixtures())

    def get_claim(self, claim_id: str) -> ClaimRecord | None:
        return self._claims.get(claim_id)

    def get_outlet(self, outlet_id: str) -> OutletRecord | None:
        return self._outlets.get(outlet_id)


def load_packaged_fixtures() -> tuple[tuple[ClaimRecord, ...], tuple[OutletRecord, ...]]:
    """Parse the fixture files shipped in trustbuilder/store/fixtures/."""
    files = resources.files("trustbuilder.store") / "fixtures"
    claims = ClaimFixtures.model_validate_json((files / "claims.json").read_bytes())
    outlets = OutletFixtures.model_validate_json((files / "outlets.json").read_bytes())
    for name, notice in (("claims.json", claims.notice), ("outlets.json", outlets.notice)):
        if not notice.startswith("FIXTURE DATA."):
            raise FixtureError(f"{name} must open its notice with 'FIXTURE DATA.'")
    return claims.claims, outlets.outlets


def _by_id[R: (ClaimRecord, OutletRecord)](records: tuple[R, ...], kind: str) -> dict[str, R]:
    index: dict[str, R] = {}
    for record in records:
        if record.id in index:
            raise FixtureError(f"duplicate {kind} id {record.id!r}")
        index[record.id] = record
    return index
