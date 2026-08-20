const tools = ['Polygon', 'Linie', 'Fläche', 'Punkt', 'Löschen']

function DrawToolbar() {
  return (
    <section className="sidebar-section" aria-labelledby="draw-toolbar-title">
      <div className="section-header">
        <h2 id="draw-toolbar-title">Werkzeuge</h2>
        <span className="badge">Folgt</span>
      </div>
      <p className="section-copy">
        Die Werkzeugleiste ist vorbereitet. Das Polygon-Zeichnen wird im nächsten
        MVP-Schritt ergänzt.
      </p>
      <div className="tool-grid">
        {tools.map((tool) => (
          <button key={tool} type="button" className="tool-button" disabled>
            {tool}
          </button>
        ))}
      </div>
    </section>
  )
}

export default DrawToolbar
