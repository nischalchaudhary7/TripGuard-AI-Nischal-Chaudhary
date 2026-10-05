from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.schemas import AssessmentRequest, AssessmentResponse
from app.config import get_settings
from app.services.assessment_service import AssessmentService
from app.utils.errors import AirportResolutionError

router = APIRouter()


@router.post("/assessments", response_model=AssessmentResponse)
async def create_assessment(payload: AssessmentRequest, request: Request, settings=Depends(get_settings)):
    try:
        service = AssessmentService(request.app.state.http_client, settings)
        return await service.assess(payload.origin, payload.destination, payload.travel_date)
    except AirportResolutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

