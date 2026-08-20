const tools = [
  { label: 'Polygon', mode: 'draw_polygon' },
  { label: 'Linie', mode: 'draw_line_string' },
  { label: 'Punkt', mode: 'draw_point' },
]

function DrawToolbar({ activeDrawMode, mapRef, onDrawModeChange }) {
  const handleMode = (mode) => () => {
    mapRef?.current?.setDrawMode(mode)
    onDrawModeChange(mode)
  }

  const handleDeleteAll = () => {
    mapRef?.current?.deleteAll()
    onDrawModeChange(null)
  }

  return (
    <section className="sidebar-section" aria-labelledby="draw-toolbar-title">
      <div className="section-header">
        <h2 id="draw-toolbar-title">Werkzeuge</h2>
        <span className="badge">Aktiv</span>
      </div>
      <p className="section-copy">
        Zeichnen Sie das Projektgebiet sowie geplante Linien- und Punktmaßnahmen
        direkt in der Karte. Die Werkzeuge funktionieren mit Maus, Touch und Stift.
      </p>
      <div className="tool-grid">
        {tools.map((tool) => (
          <button
            key={tool.mode}
            type="button"
            className={`tool-button ${activeDrawMode === tool.mode ? 'tool-button-active' : ''}`}
            onClick={handleMode(tool.mode)}
            aria-pressed={activeDrawMode === tool.mode}
          >
            {tool.label}
          </button>
        ))}
        <button type="button" className="tool-button" onClick={handleDeleteAll}>
          Löschen
        </button>
      </div>
    </section>
  )
}

export default DrawToolbar
