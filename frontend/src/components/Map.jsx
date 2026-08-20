import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

const osmStyle = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: [
        'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
      ],
      tileSize: 256,
      attribution: '© OpenStreetMap-Mitwirkende',
    },
  },
  layers: [
    {
      id: 'osm-raster',
      type: 'raster',
      source: 'osm',
    },
  ],
}

function Map() {
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return undefined
    }

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: osmStyle,
      center: [11.95, 50.02],
      zoom: 10,
      dragRotate: false,
      touchPitch: false,
      cooperativeGestures: true,
    })

    map.addControl(new maplibregl.NavigationControl(), 'top-right')
    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  return (
    <section className="map-wrapper" aria-label="Projektkarte">
      <div className="map-header">
        <div>
          <p className="eyebrow">Kartenansicht</p>
          <h2>OpenStreetMap-Grundkarte</h2>
        </div>
        <p className="map-note">
          Startansicht im Fichtelgebirge als Basis für das spätere Einzeichnen des
          Projektgebiets.
        </p>
      </div>
      <div ref={mapContainerRef} className="map-canvas" />
    </section>
  )
}

export default Map
