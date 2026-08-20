from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import geodata, hydrology, measures

app = FastAPI(
    title="Hydro-Planner API",
    version="0.1.0",
    summary="Backend scaffold for decentralised water-retention planning.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(geodata.router)
app.include_router(hydrology.router)
app.include_router(measures.router)


@app.get("/api/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
