from fastapi import APIRouter

from trustbuilder import __version__
from trustbuilder.api.deps import StoreDep
from trustbuilder.api.schemas import Health

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness check (no API key needed)")
def health(store: StoreDep) -> Health:
    return Health(version=__version__, data_status=store.data_status)
