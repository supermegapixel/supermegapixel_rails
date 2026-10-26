from fastapi import APIRouter, Request

from trustbuilder.api.deps import StoreDep, build_meta
from trustbuilder.api.errors import ERROR_RESPONSES, not_found
from trustbuilder.api.schemas import ClaimScore, ClaimScoreResponse
from trustbuilder.domain.ids import CLAIM_PREFIX

router = APIRouter(prefix="/v1/claims", tags=["claims"], responses=ERROR_RESPONSES)


@router.get(
    "/{claim_id}/score",
    summary="A claim's current verdict next to its original verdict",
    description=(
        "Returns the label, 0-100 score, band, confidence, evidence strength and receipts for "
        "the latest verdict version and for the first one. An unverifiable claim returns 200 "
        "with a null score and band `insufficient_evidence`."
    ),
)
def get_claim_score(claim_id: str, request: Request, store: StoreDep) -> ClaimScoreResponse:
    claim = store.get_claim(claim_id)
    if claim is None:
        raise not_found("claim", claim_id, CLAIM_PREFIX)
    return ClaimScoreResponse(data=ClaimScore.from_record(claim), meta=build_meta(request, store))
