from fastapi import APIRouter, Request

from trustbuilder.api.deps import StoreDep, build_meta
from trustbuilder.api.errors import ERROR_RESPONSES, not_found
from trustbuilder.api.schemas import OutletTrustIndex, OutletTrustIndexResponse
from trustbuilder.domain.ids import OUTLET_PREFIX

router = APIRouter(prefix="/v1/outlets", tags=["outlets"], responses=ERROR_RESPONSES)


@router.get(
    "/{outlet_id}/trust-index",
    summary="An outlet's current Trust Index, change since last week, and recent history",
    description=(
        "Returns the reach-weighted index (0-100) with its interval, scoring window and inputs. "
        "An outlet with too few checked claims returns 200 with status `insufficient_evidence` "
        "and a null index."
    ),
)
def get_outlet_trust_index(
    outlet_id: str, request: Request, store: StoreDep
) -> OutletTrustIndexResponse:
    outlet = store.get_outlet(outlet_id)
    if outlet is None:
        raise not_found("outlet", outlet_id, OUTLET_PREFIX)
    return OutletTrustIndexResponse(
        data=OutletTrustIndex.from_record(outlet), meta=build_meta(request, store)
    )
