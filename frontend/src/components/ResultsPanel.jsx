function ResultsPanel({ status, message }) {
  return (
    <section className="sidebar-section" aria-labelledby="results-title">
      <div className="section-header">
        <h2 id="results-title">Projektstatus</h2>
        <span className="badge badge-active">{status}</span>
      </div>
      <div className="placeholder-card">
        <p>{message}</p>
      </div>
    </section>
  )
}

export default ResultsPanel
