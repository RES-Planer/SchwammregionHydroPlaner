from pydantic import BaseModel


class Measure(BaseModel):
    id: str
    measure_type: str
    geometry: dict
