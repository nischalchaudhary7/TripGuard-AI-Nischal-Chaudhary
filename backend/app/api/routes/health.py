from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "TripGuard AI", "checked_at": datetime.now(UTC)}

