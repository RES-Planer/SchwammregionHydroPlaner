import './App.css'
import { useRef, useState } from 'react'
import DrawToolbar from './components/DrawToolbar'
import HydrographChart from './components/HydrographChart'
import Map from './components/Map'
import ResultsPanel from './components/ResultsPanel'
import useHydroSimulation from './hooks/useHydroSimulation'

function App() {
  const {
    status,
    message,
    isLoading,
    error,
    catchment,
    flowPaths,
    areaHa,
    analyzeProjectArea,
  } = useHydroSimulation()
  const mapRef = useRef(null)
  const [activeDrawMode, setActiveDrawMode] = useState(null)

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-section">
          <p className="eyebrow">Hydro-Planner MVP</p>
          <h1>Web-Frontend für dezentralen Wasserrückhalt</h1>
          <p className="intro">
            Schritt 1 des MVP stellt die Kartenbasis mit OpenStreetMap und die
            grundlegende Projektstruktur für Frontend und Backend bereit.
          </p>
        </div>

        <DrawToolbar
          activeDrawMode={activeDrawMode}
          mapRef={mapRef}
          onDrawModeChange={setActiveDrawMode}
        />
        <ResultsPanel
          areaHa={areaHa}
          error={error}
          isLoading={isLoading}
          message={message}
          status={status}
        />
        <HydrographChart />
      </aside>

      <main className="map-panel">
        <Map
          catchment={catchment}
          flowPaths={flowPaths}
          onProjectAreaDrawn={analyzeProjectArea}
          ref={mapRef}
        />
      </main>
    </div>
  )
}

export default App
