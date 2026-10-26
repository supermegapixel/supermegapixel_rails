"""The read interface the API depends on. The fixture store implements it now; a
Postgres store over the append-only tables replaces it after Phase 0 (PLAN.md §6, S0)."""

from typing import Protocol

from trustbuilder.domain.vocabulary import DataStatus
from trustbuilder.store.models import ClaimRecord, OutletRecord


class ScoreStore(Protocol):
    @property
    def data_status(self) -> DataStatus: ...

    @property
    def methodology_version(self) -> str: ...

    def get_claim(self, claim_id: str) -> ClaimRecord | None: ...

    def get_outlet(self, outlet_id: str) -> OutletRecord | None: ...
