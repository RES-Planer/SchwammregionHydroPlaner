from pydantic import BaseModel, Field


class ProjectArea(BaseModel):
    type: str = Field(default="Feature")
    geometry: dict = Field(default_factory=dict)
    properties: dict = Field(default_factory=dict)


class WatershedRequest(BaseModel):
    project_area: ProjectArea


class WatershedFeature(BaseModel):
    type: str = Field(default="Feature")
    geometry: dict
    properties: dict = Field(default_factory=dict)


class WatershedResponse(BaseModel):
    catchment: WatershedFeature
    flow_paths: list[WatershedFeature]
    area_ha: float


class DgmRequest(BaseModel):
    # GeoJSON Polygon geometry, coordinates in EPSG:25832.
    polygon: dict


class DgmResponse(BaseModel):
    status: str
    tiles_downloaded: int
    bbox: list[float]
