import { useCallback, useState } from 'react'

// Empty by default so requests go through the Vite dev proxy (or a same-origin
// reverse proxy in production) instead of a hardcoded host/port that breaks
// under remote port-forwarding setups.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
const REQUEST_TIMEOUT_MS = 180_000

function useHydroSimulation() {
  const [status, setStatus] = useState('Bereit')
  const [message, setMessage] = useState(
    'Zeichnen Sie ein Projektgebiet als Polygon, um das Einzugsgebiet automatisch zu berechnen.',
  )
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [catchment, setCatchment] = useState(null)
  const [flowPaths, setFlowPaths] = useState(null)
  const [areaHa, setAreaHa] = useState(null)

  const analyzeProjectArea = useCallback(async (polygonGeometry) => {
    setIsLoading(true)
    setError(null)
    setStatus('Berechnung läuft')
    setMessage('DGM1 wird geladen und das Einzugsgebiet wird berechnet …')

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

    try {
      const response = await fetch(`${API_BASE_URL}/api/watershed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_area: { geometry: polygonGeometry } }),
        signal: controller.signal,
      })

      if (!response.ok) {
        const body = await response.json().catch(() => null)
        // The backend already returns a complete German error message.
        throw new Error(body?.detail ?? `Backend-Fehler (HTTP ${response.status})`, {
          cause: body?.detail ? 'described' : 'undescribed',
        })
      }

      const data = await response.json()
      setCatchment(data.catchment.geometry)
      setFlowPaths(data.flow_paths.map((feature) => feature.geometry))
      setAreaHa(data.area_ha)
      setStatus('Fertig')
      setMessage(`Einzugsgebiet berechnet: ${data.area_ha.toFixed(2)} ha.`)
    } catch (caughtError) {
      let description
      if (caughtError.name === 'AbortError') {
        description = 'DGM konnte nicht geladen werden (Zeitüberschreitung).'
      } else if (caughtError.cause === 'described') {
        description = caughtError.message
      } else {
        description = `DGM konnte nicht geladen werden: ${caughtError.message}`
      }
      setError(description)
      setStatus('Fehler')
      setMessage(description)
    } finally {
      clearTimeout(timeoutId)
      setIsLoading(false)
    }
  }, [])

  return { status, message, isLoading, error, catchment, flowPaths, areaHa, analyzeProjectArea }
}

export default useHydroSimulation
