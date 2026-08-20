import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import DrawToolbar from './DrawToolbar.jsx';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';

// Fichtelgebirge-Region, Bayern – EPSG:4326 (MapLibre uses WGS84 internally)
const INITIAL_CENTER = [12.0, 50.05]; // lng, lat
const INITIAL_ZOOM = 10;

// OSM WMTS via tile URL (no API key required)
const OSM_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxzoom: 19,
    },
  },
  layers: [
    {
      id: 'osm-tiles',
      type: 'raster',
      source: 'osm',
      minzoom: 0,
      maxzoom: 22,
    },
  ],
};

export default function Map() {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const drawRef = useRef(null);

  useEffect(() => {
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: OSM_STYLE,
      center: INITIAL_CENTER,
      zoom: INITIAL_ZOOM,
      // MapLibre uses WebMercator (EPSG:3857) internally; EPSG:25832 display
      // projection can be configured server-side or via proj4 + custom projection.
      // For the MVP the tiles are rendered in Web Mercator, which is standard.
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-left');

    const draw = new MapboxDraw({
      displayControlsDefault: false,
      controls: {},
      defaultMode: 'simple_select',
      touchEnabled: true,
    });

    // MapboxDraw needs mapbox-gl-like interface; maplibre-gl is compatible.
    map.addControl(draw);
    drawRef.current = draw;
    mapRef.current = map;

    // Output polygon GeoJSON to console after drawing
    map.on('draw.create', (e) => {
      console.log('[HydroPlaner] Neues Polygon gezeichnet (GeoJSON):');
      console.log(JSON.stringify(e.features, null, 2));
    });

    map.on('draw.update', (e) => {
      console.log('[HydroPlaner] Polygon aktualisiert (GeoJSON):');
      console.log(JSON.stringify(e.features, null, 2));
    });

    return () => {
      map.remove();
      mapRef.current = null;
      drawRef.current = null;
    };
  }, []);

  const handleModeChange = (mode) => {
    if (drawRef.current) {
      drawRef.current.changeMode(mode);
    }
  };

  const handleDeleteAll = () => {
    if (drawRef.current) {
      drawRef.current.deleteAll();
    }
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
      <DrawToolbar onModeChange={handleModeChange} onDeleteAll={handleDeleteAll} />
    </div>
  );
}
