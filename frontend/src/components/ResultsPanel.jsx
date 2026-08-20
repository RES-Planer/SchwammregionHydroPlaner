function ResultsPanel({ areaHa, error, isLoading, message, status }) {
  return (
    <section className="sidebar-section" aria-labelledby="results-title">
      <div className="section-header">
        <h2 id="results-title">Projektstatus</h2>
        <span className={`badge ${error ? 'badge-error' : 'badge-active'}`}>{status}</span>
      </div>
      <div className="placeholder-card">
        {isLoading && <div className="spinner" aria-label="Berechnung läuft" role="status" />}
        <p className={error ? 'error-text' : undefined}>{message}</p>
        {areaHa != null && !error && (
          <p className="area-value">
            Fläche Einzugsgebiet: <strong>{areaHa.toFixed(2)} ha</strong>
          </p>
        )}
      </div>
    </section>
  )
}

export default ResultsPanel
