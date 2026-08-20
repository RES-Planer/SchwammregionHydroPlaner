"""Exercises the /api/watershed endpoint end-to-end with a synthetic DEM,
bypassing the real LDBV WCS network call via monkeypatching."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from fastapi.testclient import TestClient
from pyproj import Transformer
from rasterio.transform import from_origin

from app.main import app
from app.services import dgm_service

client = TestClient(app)

UTM_ORIGIN_X = 700_000.0
UTM_ORIGIN_Y = 5_540_000.0
GRID_SIZE = 200

_TO_WGS84 = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)
_HALF_EXTENT_DEG = 0.0005
_POUR_LON, _POUR_LAT = _TO_WGS84.transform(
    UTM_ORIGIN_X + GRID_SIZE * 0.6, UTM_ORIGIN_Y - GRID_SIZE * 0.6
)
# A small polygon inside the synthetic raster's extent used by the test DEM
# below, standing in for a polygon drawn near Wunsiedel in the real app.
WUNSIEDEL_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [_POUR_LON - _HALF_EXTENT_DEG, _POUR_LAT - _HALF_EXTENT_DEG],
            [_POUR_LON + _HALF_EXTENT_DEG, _POUR_LAT - _HALF_EXTENT_DEG],
            [_POUR_LON + _HALF_EXTENT_DEG, _POUR_LAT + _HALF_EXTENT_DEG],
            [_POUR_LON - _HALF_EXTENT_DEG, _POUR_LAT + _HALF_EXTENT_DEG],
            [_POUR_LON - _HALF_EXTENT_DEG, _POUR_LAT - _HALF_EXTENT_DEG],
        ]
    ],
}


def _write_synthetic_valley_dem(path: Path) -> None:
    rows = np.arange(GRID_SIZE)
    cols = np.arange(GRID_SIZE)
    col_grid, row_grid = np.meshgrid(cols, rows)
    distance_from_outlet = row_grid + col_grid
    valley_trough = np.abs(row_grid - col_grid) * 0.05
    elevation = (distance_from_outlet * 0.2 + valley_trough).astype("float32")

    transform = from_origin(UTM_ORIGIN_X, UTM_ORIGIN_Y, 1.0, 1.0)
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


def test_watershed_endpoint_returns_catchment(tmp_path, monkeypatch):
    dem_path = tmp_path / "synthetic_dem.tif"
    _write_synthetic_valley_dem(dem_path)
    monkeypatch.setattr(dgm_service, "fetch_dgm1_tiles", lambda *args, **kwargs: [dem_path])
    monkeypatch.setattr(dgm_service, "merge_tiles", lambda *args, **kwargs: dem_path)

    response = client.post("/api/watershed", json={"project_area": {"geometry": WUNSIEDEL_POLYGON}})

    assert response.status_code == 200
    body = response.json()
    assert body["area_ha"] > 0
    assert body["catchment"]["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert isinstance(body["flow_paths"], list)


def test_dgm_endpoint_returns_tile_count(monkeypatch):
    monkeypatch.setattr(
        dgm_service,
        "fetch_dgm1_tiles",
        lambda polygon: [Path("/tmp/dgm_cache/689_5559.tif"), Path("/tmp/dgm_cache/690_5559.tif")],
    )

    polygon_utm = {
        "type": "Polygon",
        "coordinates": [
            [
                [689000, 5559000],
                [692000, 5559000],
                [692000, 5562000],
                [689000, 5562000],
                [689000, 5559000],
            ]
        ],
    }

    response = client.post("/api/dgm", json={"polygon": polygon_utm})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["tiles_downloaded"] == 2
    assert body["bbox"] == [689000, 5559000, 692000, 5562000]


def test_watershed_endpoint_reports_dgm_download_failure(monkeypatch):
    def _raise_download_error(*_args, **_kwargs):
        raise dgm_service.DgmDownloadError("timed out")

    monkeypatch.setattr(dgm_service, "fetch_dgm1_tiles", _raise_download_error)

    response = client.post("/api/watershed", json={"project_area": {"geometry": WUNSIEDEL_POLYGON}})

    assert response.status_code == 504
    assert "DGM konnte nicht geladen werden" in response.json()["detail"]
