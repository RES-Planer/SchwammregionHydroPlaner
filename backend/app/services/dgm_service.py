"""Download DGM1 (1 m digital terrain model) tiles for a polygon from the
Bavarian LDBV OpenData portal, in ETRS89 / UTM zone 32N (EPSG:25832).

There is no public WCS for this dataset. Tiles are resolved via the
"poly2metalink" service (the same one used by geodaten.bayern.de/opengeodata)
and downloaded directly from the bayernwolke CDN, then merged and clipped
with rasterio.
"""

from __future__ import annotations

import hashlib
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import rasterio
import requests
from rasterio.mask import mask as rasterio_mask
from rasterio.merge import merge as rasterio_merge

POLY2METALINK_METALINK_URL = "https://geoservices.bayern.de/services/poly2metalink/metalink/dgm1"
# Single-point elevation fallback per the task spec. Returned "404 Route Not
# Found" for every path/parameter combination tried during implementation —
# double-check this URL against current LDBV documentation before relying on it.
HOEHEN_FALLBACK_URL = "https://geoservices.bayern.de/bvvapi/od/hoehen"

CACHE_DIR = Path("/tmp/dgm_cache")
MERGED_CACHE_DIR = CACHE_DIR / "merged"
REQUEST_TIMEOUT_SECONDS = (5, 30)

_FILE_ENTRY_PATTERN = re.compile(r'<file name="([^"]+)">\s*<url>([^<]+)</url>')


class DgmDownloadError(RuntimeError):
    """Raised when DGM1 tiles could not be retrieved for the given polygon."""


def _polygon_to_ewkt(polygon) -> str:
    ring = ",".join(f"{x} {y}" for x, y in polygon.exterior.coords)
    return f"SRID=25832;MULTIPOLYGON((({ring})))"


def resolve_tiles(polygon) -> list[tuple[str, str]]:
    """Ask poly2metalink which DGM1 tiles (name, download URL) cover `polygon`
    (a shapely geometry in EPSG:25832)."""
    ewkt = _polygon_to_ewkt(polygon)
    try:
        response = requests.post(
            POLY2METALINK_METALINK_URL,
            data=ewkt.encode("utf-8"),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DgmDownloadError(f"Kachel-Index konnte nicht abgefragt werden: {exc}") from exc

    tiles = _FILE_ENTRY_PATTERN.findall(response.text)
    if not tiles:
        raise DgmDownloadError("Für das Projektgebiet wurden keine DGM1-Kacheln gefunden.")
    return tiles


def _download_tile(name: str, url: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    destination = CACHE_DIR / name
    if destination.exists():
        return destination

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DgmDownloadError(f"Kachel '{name}' konnte nicht geladen werden: {exc}") from exc

    if "tiff" not in response.headers.get("Content-Type", "").lower():
        raise DgmDownloadError(f"Kachel '{name}' enthielt kein gültiges GeoTIFF.")

    # Write atomically so a failed/partial download never poisons the cache.
    tmp_path = destination.with_suffix(".tmp")
    tmp_path.write_bytes(response.content)
    tmp_path.rename(destination)
    return destination


def fetch_dgm1_tiles(polygon) -> list[Path]:
    """Resolve and download (or reuse cached copies of) all DGM1 tiles
    covering `polygon` (a shapely geometry in EPSG:25832)."""
    tiles = resolve_tiles(polygon)
    with ThreadPoolExecutor(max_workers=min(4, len(tiles))) as executor:
        futures = [executor.submit(_download_tile, name, url) for name, url in tiles]
        return [future.result() for future in futures]


def _merge_cache_path(tile_paths: list[Path], suffix: str) -> Path:
    key = ",".join(sorted(path.name for path in tile_paths)) + suffix
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return MERGED_CACHE_DIR / f"{digest}.tif"


def merge_tiles(tile_paths: list[Path]) -> Path:
    """Merge multiple DGM1 tiles into a single GeoTIFF, without clipping."""
    MERGED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    destination = _merge_cache_path(tile_paths, suffix="_merged")
    if destination.exists():
        return destination

    datasets = [rasterio.open(path) for path in tile_paths]
    try:
        mosaic, transform = rasterio_merge(datasets)
        profile = datasets[0].profile
    finally:
        for dataset in datasets:
            dataset.close()

    profile.update(height=mosaic.shape[1], width=mosaic.shape[2], transform=transform)
    with rasterio.open(destination, "w", **profile) as out:
        out.write(mosaic)
    return destination


def merge_and_clip_tiles(tile_paths: list[Path], polygon) -> Path:
    """Merge DGM1 tiles and clip the result to `polygon` (EPSG:25832)."""
    MERGED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    destination = _merge_cache_path(tile_paths, suffix="_clipped")
    if destination.exists():
        return destination

    merged_path = merge_tiles(tile_paths)
    with rasterio.open(merged_path) as dataset:
        clipped, transform = rasterio_mask(dataset, [polygon.__geo_interface__], crop=True)
        profile = dataset.profile

    profile.update(height=clipped.shape[1], width=clipped.shape[2], transform=transform)
    with rasterio.open(destination, "w", **profile) as out:
        out.write(clipped)
    return destination


def fetch_elevation_fallback(x: float, y: float) -> float:
    """Fall back to the single-point height API when tile downloads fail."""
    try:
        response = requests.get(
            HOEHEN_FALLBACK_URL,
            params={"east": x, "north": y},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise DgmDownloadError(f"Höhen-Fallback-Dienst nicht erreichbar: {exc}") from exc

    elevation = payload.get("hoehe") or payload.get("h") or payload.get("z")
    if elevation is None:
        raise DgmDownloadError("Höhen-Fallback-Dienst lieferte keinen Höhenwert.")
    return float(elevation)
