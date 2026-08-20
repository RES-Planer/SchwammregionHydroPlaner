from fastapi import APIRouter, HTTPException, status

from app.models.project import WatershedRequest

router = APIRouter(prefix="/api", tags=["hydrology"])


@router.post("/watershed")
def derive_watershed(_payload: WatershedRequest) -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Watershed derivation will be added in the next MVP step.",
    )
