from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import watershed

app = FastAPI(
    title="HydroPlaner API",
    description="Hydrologische Planung – Schwammregion Backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(watershed.router, prefix="/api/watershed", tags=["watershed"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
