from pydantic import BaseModel, Field


class ProjectArea(BaseModel):
    type: str = Field(default="Feature")
    geometry: dict = Field(default_factory=dict)
    properties: dict = Field(default_factory=dict)


class WatershedRequest(BaseModel):
    project_area: ProjectArea
