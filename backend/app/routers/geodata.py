from fastapi import APIRouter

router = APIRouter(prefix="/api/geodata", tags=["geodata"])


@router.get("/status")
def geodata_status() -> dict[str, str]:
    return {"status": "planned"}
