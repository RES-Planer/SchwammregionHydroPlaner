import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import MapboxDraw from '@mapbox/mapbox-gl-draw'
import 'maplibre-gl/dist/maplibre-gl.css'
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css'

const topoStyle = {
  version: 8,
  sources: {
    topo: {
      type: 'raster',
      tiles: ['https://tile.opentopomap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: 'Kartendaten: © OpenStreetMap-Mitwirkende, SRTM | Kartendarstellung: © OpenTopoMap (CC-BY-SA)',
    },
  },
  layers: [
    {
      id: 'topo-raster',
      type: 'raster',
      source: 'topo',
    },
  ],
}

const emptyFeatureCollection = () => ({ type: 'FeatureCollection', features: [] })

const Map = forwardRef(function Map({ catchment, flowPaths, onProjectAreaDrawn }, ref) {
  const mapContainerRef = useRef(null)
  const mapRef = useRef(null)
  const drawRef = useRef(null)
  const pendingModeRef = useRef(null)
  const onProjectAreaDrawnRef = useRef(onProjectAreaDrawn)

  useEffect(() => {
    onProjectAreaDrawnRef.current = onProjectAreaDrawn
  }, [onProjectAreaDrawn])

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return undefined
    }

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: topoStyle,
      center: [11.95, 50.02],
      zoom: 10,
      dragRotate: false,
      touchPitch: false,
      cooperativeGestures: false,
    })

    map.addControl(new maplibregl.NavigationControl(), 'top-right')

    // MapLibre requires literal arrays inside the line-dasharray expression.
    // Recolour the drawn project-area outline/fill to a clearly visible orange.
    const drawStyles = MapboxDraw.lib.theme.map((layer) => {
      if (layer.id === 'gl-draw-polygon-fill') {
        return {
          ...layer,
          paint: { ...layer.paint, 'fill-color': '#ff6b35', 'fill-opacity': 0.1 },
        }
      }
      if (layer.id === 'gl-draw-lines') {
        return {
          ...layer,
          paint: {
            ...layer.paint,
            'line-color': '#ff6b35',
            'line-width': 2,
            'line-dasharray': [
              'case',
              ['==', ['get', 'active'], 'true'],
              ['literal', [0.2, 2]],
              ['literal', [2, 0]],
            ],
          },
        }
      }
      return layer
    })

    const draw = new MapboxDraw({
      displayControlsDefault: false,
      controls: {},
      styles: drawStyles,
    })
    map.addControl(draw)
    drawRef.current = draw
    if (pendingModeRef.current) {
      draw.changeMode(pendingModeRef.current)
    }

    const handleDrawCreate = (event) => {
      const feature = event.features?.[0]
      if (feature?.geometry?.type === 'Polygon') {
        console.log('Polygon gezeichnet:', feature)
        onProjectAreaDrawnRef.current?.(feature.geometry)
      }
    }

    map.on('load', () => {
      console.log('MapLibre GL Draw initialisiert')

      map.addSource('catchment', { type: 'geojson', data: emptyFeatureCollection() })
      map.addLayer({
        id: 'catchment-fill',
        type: 'fill',
        source: 'catchment',
        paint: { 'fill-color': '#7fbfff', 'fill-opacity': 0.15 },
      })
      map.addLayer({
        id: 'catchment-outline',
        type: 'line',
        source: 'catchment',
        paint: { 'line-color': '#1a3a6b', 'line-width': 2 },
      })

      map.addSource('flow-paths', { type: 'geojson', data: emptyFeatureCollection() })
      map.addLayer({
        id: 'flow-paths-line',
        type: 'line',
        source: 'flow-paths',
        paint: { 'line-color': '#00b4d8', 'line-width': 1.5 },
      })
    })
    map.on('draw.create', handleDrawCreate)
    map.on('draw.update', handleDrawCreate)

    mapRef.current = map

    return () => {
      map.off('draw.create', handleDrawCreate)
      map.off('draw.update', handleDrawCreate)
      map.remove()
      mapRef.current = null
      drawRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) {
      return
    }

    const updateSources = () => {
      map
        .getSource('catchment')
        ?.setData(catchment ? { type: 'Feature', geometry: catchment, properties: {} } : emptyFeatureCollection())
      map.getSource('flow-paths')?.setData({
        type: 'FeatureCollection',
        features: (flowPaths ?? []).map((geometry) => ({ type: 'Feature', geometry, properties: {} })),
      })
    }

    if (map.isStyleLoaded()) {
      updateSources()
    } else {
      map.once('load', updateSources)
    }
  }, [catchment, flowPaths])

  useImperativeHandle(
    ref,
    () => ({
      setDrawMode(mode) {
        pendingModeRef.current = mode
        drawRef.current?.changeMode(mode)
        mapRef.current?.getCanvas().style.setProperty('cursor', 'crosshair')
      },
      deleteAll() {
        drawRef.current?.deleteAll()
        pendingModeRef.current = null
        mapRef.current?.getCanvas().style.removeProperty('cursor')
      },
      getAll() {
        return drawRef.current?.getAll()
      },
    }),
    [],
  )

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
})

export default Map
