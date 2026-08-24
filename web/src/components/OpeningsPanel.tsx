import { fetchOpenings } from '../api'
import type { Opening } from '../types'
import { useApi } from '../useApi'

function formatSlot(opening: Opening): string {
  const start = new Date(opening.start)
  const end = new Date(opening.end)
  const day = start.toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
  const from = start.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  })
  const to = end.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  })
  return `${day} · ${from}–${to}`
}

export function OpeningsPanel() {
  const { data, error, loading } = useApi<Opening[]>(fetchOpenings)

  if (loading) {
    return <p className="note">Loading openings…</p>
  }
  if (error) {
    return <p className="note error">Could not load openings: {error}</p>
  }
  if (!data || data.length === 0) {
    return <p className="note">No courts are open in the latest snapshot.</p>
  }

  return (
    <div>
      <p className="note">
        Bookable slots in the most recent stored snapshot.
      </p>
      <ul className="openings">
        {data.map((opening) => (
          <li key={`${opening.court}-${opening.start}`}>
            <span className="court">{opening.court}</span>
            <span className="mono">{formatSlot(opening)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}