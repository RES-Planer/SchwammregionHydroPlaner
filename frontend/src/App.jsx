import './App.css'
import DrawToolbar from './components/DrawToolbar'
import HydrographChart from './components/HydrographChart'
import Map from './components/Map'
import ResultsPanel from './components/ResultsPanel'
import useHydroSimulation from './hooks/useHydroSimulation'

function App() {
  const { status, message } = useHydroSimulation()

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

        <DrawToolbar />
        <ResultsPanel status={status} message={message} />
        <HydrographChart />
      </aside>

      <main className="map-panel">
        <Map />
      </main>
    </div>
  )
}

export default App
