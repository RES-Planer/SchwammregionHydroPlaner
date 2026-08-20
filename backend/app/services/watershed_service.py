"""Derive a catchment area from a DGM1 raster, following the D8 depression
filling / flow direction / accumulation workflow described by Gehr (2025):
ETRS89 / UTM zone 32N (EPSG:25832), DGM1 with 1 m resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

# pysheds 0.5 still calls the numpy<2 alias `np.in1d`, removed in numpy 2.0.
if not hasattr(np, "in1d"):
    np.in1d = np.isin

from pyproj import Transformer
from pysheds.grid import Grid
from shapely.geometry import mapping, shape
from shapely.ops import transform as shapely_transform, unary_union

SOURCE_CRS = "EPSG:4326"
WORKING_CRS = "EPSG:25832"
# D8 flow direction encoding used throughout the pysheds pipeline below.
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)
# Minimum contributing cells (~ m^2 at 1 m resolution) before a cell counts
# as a flow path for the river-network extraction.
FLOW_ACCUMULATION_THRESHOLD = 500


class WatershedDelineationError(RuntimeError):
    """Raised when the watershed could not be derived from the DGM1 raster."""


def _to_working_crs(geometry):
    transformer = Transformer.from_crs(SOURCE_CRS, WORKING_CRS, always_xy=True)
    return shapely_transform(transformer.transform, geometry)


def _to_source_crs(geometry):
    transformer = Transformer.from_crs(WORKING_CRS, SOURCE_CRS, always_xy=True)
    return shapely_transform(transformer.transform, geometry)


def delineate_watershed(dem_path: Path, project_area_geometry: dict) -> dict[str, Any]:
    """Compute the catchment draining to the centroid of the drawn polygon.

    Returns a dict with the catchment polygon, the flow paths inside it and
    the catchment area in hectares, all geometries in EPSG:4326.
    """
    polygon_wgs84 = shape(project_area_geometry)
    if polygon_wgs84.is_empty:
        raise WatershedDelineationError("Das Projektgebiet enthält keine gültige Geometrie.")

    polygon_utm = _to_working_crs(polygon_wgs84)
    pour_point = polygon_utm.centroid

    grid = Grid.from_raster(str(dem_path))
    dem = grid.read_raster(str(dem_path))

    # 1. Senkenfüllung
    filled_dem = grid.fill_pits(dem)
    filled_dem = grid.fill_depressions(filled_dem)
    inflated_dem = grid.resolve_flats(filled_dem)

    # 2. Fließrichtung
    flow_dir = grid.flowdir(inflated_dem, dirmap=DIRMAP)

    # 3. Fließakkumulation
    accumulation = grid.accumulation(flow_dir, dirmap=DIRMAP)

    # 4. Einzugsgebiet ab dem Polygon-Schwerpunkt
    catchment = grid.catchment(
        x=pour_point.x,
        y=pour_point.y,
        fdir=flow_dir,
        dirmap=DIRMAP,
        xytype="coordinate",
    )

    grid.clip_to(catchment)
    catchment_view = grid.view(catchment)

    catchment_polygons = [
        shape(geometry) for geometry, value in grid.polygonize(catchment_view.astype("int32")) if value == 1
    ]
    if not catchment_polygons:
        raise WatershedDelineationError(
            "Für den gewählten Punkt konnte kein Einzugsgebiet abgeleitet werden."
        )

    catchment_union_utm = unary_union(catchment_polygons)
    area_ha = catchment_union_utm.area / 10_000
    catchment_wgs84 = _to_source_crs(catchment_union_utm)

    river_network = grid.extract_river_network(
        flow_dir, accumulation > FLOW_ACCUMULATION_THRESHOLD, dirmap=DIRMAP
    )
    flow_paths_wgs84 = [
        mapping(_to_source_crs(shape(feature["geometry"])))
        for feature in river_network.get("features", [])
    ]

    return {
        "catchment": mapping(catchment_wgs84),
        "flow_paths": flow_paths_wgs84,
        "area_ha": round(area_ha, 2),
    }
