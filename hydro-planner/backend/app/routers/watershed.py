"""
Watershed delineation router.

Accepts a GeoJSON point (outlet) and returns the delineated catchment polygon
using pysheds. For the MVP the DEM must be provided as a local GeoTIFF file
mounted into the container at /data/dem.tif.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import geopandas as gpd
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from shapely.geometry import shape, mapping

DEM_PATH = Path("/data/dem.tif")

router = APIRouter()


class OutletPoint(BaseModel):
    """GeoJSON Point geometry for the outlet location."""
    type: str = "Point"
    coordinates: list[float]  # [longitude, latitude]


@router.post("/delineate", summary="Einzugsgebiet berechnen")
def delineate_watershed(outlet: OutletPoint) -> dict[str, Any]:
    """
    Delineate the watershed upstream of *outlet* using pysheds.

    Requires a DEM GeoTIFF at /data/dem.tif (EPSG:25832 recommended).
    Returns a GeoJSON FeatureCollection with the catchment polygon.
    """
    if not DEM_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="DEM not available. Mount a GeoTIFF at /data/dem.tif.",
        )

    try:
        from pysheds.grid import Grid  # lazy import – heavy dependency

        grid = Grid.from_raster(str(DEM_PATH))
        dem = grid.read_raster(str(DEM_PATH))

        # Condition DEM
        pit_filled = grid.fill_pits(dem)
        flooded = grid.fill_depressions(pit_filled)
        inflated = grid.resolve_flats(flooded)

        # Flow direction (D8)
        dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
        fdir = grid.flowdir(inflated, dirmap=dirmap)

        # Accumulation
        acc = grid.accumulation(fdir, dirmap=dirmap)

        lng, lat = outlet.coordinates
        # Snap to highest accumulation within 500 m search radius
        x, y = lng, lat
        x_snap, y_snap = grid.snap_to_mask(acc > 1000, (x, y))

        # Delineate
        catch = grid.catchment(x=x_snap, y=y_snap, fdir=fdir, dirmap=dirmap, xytype="coordinate")
        grid.clip_to(catch)
        catch_view = grid.view(catch, dtype=bool)

        shapes = grid.polygonize(catch_view)
        features = [
            {"type": "Feature", "geometry": mapping(shape(geom)), "properties": {}}
            for geom, _ in shapes
        ]

        return {"type": "FeatureCollection", "features": features}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/upload-dem", summary="DEM hochladen (GeoTIFF)")
async def upload_dem(file: UploadFile = File(...)) -> dict[str, str]:
    """Upload a DEM GeoTIFF. Saved to /data/dem.tif inside the container."""
    DEM_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    DEM_PATH.write_bytes(content)
    return {"status": "ok", "path": str(DEM_PATH), "size_bytes": len(content)}
