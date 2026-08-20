# SchwammregionHydroPlaner

Web-basiertes GIS-Frontend für hydrologische Planung in der Fichtelgebirge-Region (Bayern).

## Stack

| Schicht | Technologie |
|---------|-------------|
| Frontend | React 18 + Vite + MapLibre GL JS + @mapbox/mapbox-gl-draw |
| Backend | Python 3.12 + FastAPI + pysheds + geopandas + rasterio |
| Datenbank | PostgreSQL 16 + PostGIS 3.4 |
| Deployment | Docker + Docker Compose |

## Schnellstart

```bash
cd hydro-planner
docker compose up
```

Öffne danach **http://localhost:5173** im Browser.

## MVP-Funktionen

1. OSM-Karte (kein API-Key) öffnet sich automatisch mit Fichtelgebirge als Startansicht
2. Koordinatensystem ETRS89 / UTM zone 32N (EPSG:25832) intern
3. Polygon-Zeichenwerkzeug (Maus, Touch, Stift) über die Toolbar links oben
4. Nach dem Zeichnen: GeoJSON-Ausgabe in der Browser-Konsole
5. Backend-API unter **http://localhost:8000/docs**

## Projektstruktur

```
hydro-planner/
├── frontend/          React-App (Vite Dev-Server)
│   └── src/
│       └── components/
│           ├── Map.jsx          Hauptkarte
│           └── DrawToolbar.jsx  Zeichenwerkzeuge
├── backend/           FastAPI-Backend
│   └── app/
│       ├── main.py
│       └── routers/
│           └── watershed.py    Einzugsgebiet-Berechnung (pysheds)
└── docker-compose.yml
```

## Einzugsgebiet-Berechnung

Für die Einzugsgebiet-Delineation wird ein DEM (GeoTIFF, EPSG:25832) benötigt.  
Hochladen über die API:

```bash
curl -X POST http://localhost:8000/api/watershed/upload-dem \
  -F "file=@mein_dem.tif"
```

Dann Berechnung mit einem Outlet-Punkt:

```bash
curl -X POST http://localhost:8000/api/watershed/delineate \
  -H "Content-Type: application/json" \
  -d '{"type":"Point","coordinates":[11.92,50.05]}'
```
