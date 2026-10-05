from datetime import date

from pydantic import BaseModel, Field

from app.core.models.assessment import Assessment


class AssessmentRequest(BaseModel):
    origin: str = Field(min_length=1, examples=["DFW"])
    destination: str = Field(min_length=1, examples=["DEN"])
    travel_date: date


class AssessmentResponse(Assessment):
    pass

