from fastapi import APIRouter, HTTPException, status
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform as shapely_transform

from app.models.project import (
    DgmRequest,
    DgmResponse,
    WatershedFeature,
    WatershedRequest,
    WatershedResponse,
)
from app.services import dgm_service, watershed_service

router = APIRouter(prefix="/api", tags=["hydrology"])

_TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
# Extra margin around the drawn polygon so the downloaded DGM1 tiles cover the
# whole catchment, not just the project area itself.
BBOX_BUFFER_METERS = 300


@router.post("/watershed", response_model=WatershedResponse)
def derive_watershed(payload: WatershedRequest) -> WatershedResponse:
    polygon_wgs84 = shape(payload.project_area.geometry)
    if polygon_wgs84.is_empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Das Projektgebiet enthält keine gültige Geometrie.",
        )

    polygon_utm = shapely_transform(_TO_UTM.transform, polygon_wgs84)
    buffered_polygon_utm = polygon_utm.buffer(BBOX_BUFFER_METERS)

    try:
        tile_paths = dgm_service.fetch_dgm1_tiles(buffered_polygon_utm)
        dem_path = dgm_service.merge_tiles(tile_paths)
    except dgm_service.DgmDownloadError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"DGM konnte nicht geladen werden: {exc}",
        ) from exc

    try:
        result = watershed_service.delineate_watershed(dem_path, payload.project_area.geometry)
    except watershed_service.WatershedDelineationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return WatershedResponse(
        catchment=WatershedFeature(geometry=result["catchment"]),
        flow_paths=[WatershedFeature(geometry=geometry) for geometry in result["flow_paths"]],
        area_ha=result["area_ha"],
    )


@router.post("/dgm", response_model=DgmResponse)
def download_dgm(payload: DgmRequest) -> DgmResponse:
    polygon = shape(payload.polygon)
    if polygon.is_empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Das Polygon enthält keine gültige Geometrie.",
        )

    try:
        tile_paths = dgm_service.fetch_dgm1_tiles(polygon)
    except dgm_service.DgmDownloadError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"DGM konnte nicht geladen werden: {exc}",
        ) from exc

    return DgmResponse(status="ok", tiles_downloaded=len(tile_paths), bbox=list(polygon.bounds))
