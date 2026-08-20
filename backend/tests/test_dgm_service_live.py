"""Live integration test against the real LDBV poly2metalink + bayernwolke
download services, using the Fichtelgebirge test polygon from the task spec.
Requires outbound internet access."""

from __future__ import annotations

from shapely.geometry import Polygon

from app.services import dgm_service

FICHTELGEBIRGE_POLYGON_UTM = Polygon(
    [
        (689000, 5559000),
        (692000, 5559000),
        (692000, 5562000),
        (689000, 5562000),
        (689000, 5559000),
    ]
)


def test_resolve_tiles_returns_expected_count():
    tiles = dgm_service.resolve_tiles(FICHTELGEBIRGE_POLYGON_UTM)
    assert 4 <= len(tiles) <= 9


def test_fetch_dgm1_tiles_downloads_real_geotiffs():
    tile_paths = dgm_service.fetch_dgm1_tiles(FICHTELGEBIRGE_POLYGON_UTM)
    assert 4 <= len(tile_paths) <= 9
    for path in tile_paths:
        assert path.exists()
        assert path.stat().st_size > 0

    merged_path = dgm_service.merge_tiles(tile_paths)
    assert merged_path.exists()

    clipped_path = dgm_service.merge_and_clip_tiles(tile_paths, FICHTELGEBIRGE_POLYGON_UTM)
    assert clipped_path.exists()
