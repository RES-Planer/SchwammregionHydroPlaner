"""Verifies the pysheds-based watershed pipeline end-to-end on a synthetic DEM,
independent of network access to the real LDBV WCS service."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin

from app.services.watershed_service import delineate_watershed

UTM_ORIGIN_X = 700_000.0
UTM_ORIGIN_Y = 5_540_000.0
RESOLUTION_M = 1.0
GRID_SIZE = 200


def _write_synthetic_valley_dem(path: Path) -> None:
    """A V-shaped valley draining toward the lower-left corner, so a
    catchment delineated from a pour point near the outlet is well-defined."""
    rows = np.arange(GRID_SIZE)
    cols = np.arange(GRID_SIZE)
    col_grid, row_grid = np.meshgrid(cols, rows)

    # Elevation rises with distance from the diagonal outlet corner and adds
    # a small valley trough so flow converges instead of spreading evenly.
    distance_from_outlet = row_grid + col_grid
    valley_trough = np.abs(row_grid - col_grid) * 0.05
    elevation = (distance_from_outlet * 0.2 + valley_trough).astype("float32")

    transform = from_origin(UTM_ORIGIN_X, UTM_ORIGIN_Y, RESOLUTION_M, RESOLUTION_M)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=GRID_SIZE,
        width=GRID_SIZE,
        count=1,
        dtype="float32",
        crs="EPSG:25832",
        transform=transform,
        nodata=-9999.0,
    ) as dataset:
        dataset.write(elevation, 1)


def test_delineate_watershed_returns_plausible_catchment(tmp_path):
    dem_path = tmp_path / "synthetic_dem.tif"
    _write_synthetic_valley_dem(dem_path)

    # Pour point near the outlet corner, in UTM coordinates converted to WGS84
    # since the service expects the drawn polygon in EPSG:4326.
    to_wgs84 = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)
    pour_x = UTM_ORIGIN_X + GRID_SIZE * RESOLUTION_M * 0.6
    pour_y = UTM_ORIGIN_Y - GRID_SIZE * RESOLUTION_M * 0.6
    lon, lat = to_wgs84.transform(pour_x, pour_y)

    half_extent_deg = 0.0005
    project_area_geometry = {
        "type": "Polygon",
        "coordinates": [
            [
                [lon - half_extent_deg, lat - half_extent_deg],
                [lon + half_extent_deg, lat - half_extent_deg],
                [lon + half_extent_deg, lat + half_extent_deg],
                [lon - half_extent_deg, lat + half_extent_deg],
                [lon - half_extent_deg, lat - half_extent_deg],
            ]
        ],
    }

    result = delineate_watershed(dem_path, project_area_geometry)

    assert result["area_ha"] > 0
    assert result["catchment"]["type"] in ("Polygon", "MultiPolygon")
    assert isinstance(result["flow_paths"], list)
