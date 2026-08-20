from fastapi import APIRouter

router = APIRouter(prefix="/api/measures", tags=["measures"])


@router.get("/status")
def measures_status() -> dict[str, str]:
    return {"status": "planned"}
