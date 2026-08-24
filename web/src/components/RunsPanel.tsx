import { Fragment, useState } from 'react'
import { fetchRuns } from '../api'
import type { Run } from '../types'
import { useApi } from '../useApi'

function statusClass(status: string): string {
  if (status === 'ok') {
    return 'badge ok'
  }
  if (status === 'notify_failed') {
    return 'badge warn'
  }
  return 'badge bad'
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function RunsPanel() {
  const { data, error, loading } = useApi<Run[]>(fetchRuns)
  const [expanded, setExpanded] = useState<number | null>(null)

  if (loading) {
    return <p className="note">Loading poll history…</p>
  }
  if (error) {
    return <p className="note error">Could not load runs: {error}</p>
  }
  if (!data || data.length === 0) {
    return <p className="note">No polls recorded yet.</p>
  }

  let maxSlots = 1
  for (const run of data) {
    if (run.slot_count > maxSlots) {
      maxSlots = run.slot_count
    }
  }

  return (
    <div>
      <p className="note">
        Every poll attempt is recorded, successful or not. Failed runs carry a
        triage verdict — click one to read it.
      </p>

      <table className="runs">
        <thead>
          <tr>
            <th>When</th>
            <th>Status</th>
            <th>Slots seen</th>
            <th>Opened</th>
            <th>Alerts</th>
            <th>Triage</th>
          </tr>
        </thead>
        <tbody>
          {data.map((run) => {
            const isOpen = expanded === run.id
            const canExpand = run.triage !== null || run.error_message !== null

            return (
              <Fragment key={run.id}>
                <tr
                  className={canExpand ? 'clickable' : ''}
                  onClick={() => setExpanded(isOpen ? null : run.id)}
                >
                  <td className="mono">{formatTime(run.started_at)}</td>
                  <td>
                    <span className={statusClass(run.status)}>{run.status}</span>
                  </td>
                  <td>
                    <div className="bar-wrap">
                      <div
                        className="bar"
                        style={{ width: `${(run.slot_count / maxSlots) * 100}%` }}
                      />
                      <span className="mono">{run.slot_count}</span>
                    </div>
                  </td>
                  <td className="mono">{run.opened_count}</td>
                  <td className="mono">{run.alerts_sent}</td>
                  <td>
                    {run.triage ? (
                      <span className="badge triage">
                        {run.triage.category}
                        {run.triage.needs_human ? ' · needs human' : ''}
                      </span>
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </td>
                </tr>

                {isOpen && canExpand && (
                  <tr className="detail">
                    <td colSpan={6}>
                      {run.error_message && (
                        <p>
                          <strong>{run.error_type}</strong>: {run.error_message}
                        </p>
                      )}
                      {run.triage && (
                        <>
                          <p>{run.triage.summary}</p>
                          <p className="muted mono">
                            {run.triage.source} · confidence{' '}
                            {run.triage.confidence.toFixed(2)} ·{' '}
                            {formatTime(run.triage.triaged_at)}
                          </p>
                        </>
                      )}
                    </td>
                  </tr>
                )}
              </Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
