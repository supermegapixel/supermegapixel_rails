"""Score storage. The API reads through the ScoreStore interface only."""

from trustbuilder.config import Settings
from trustbuilder.store.base import ScoreStore
from trustbuilder.store.fixture_store import FixtureStore

__all__ = ["ScoreStore", "build_store"]


def build_store(settings: Settings) -> ScoreStore:
    match settings.store:
        case "fixture":
            return FixtureStore.from_package()
