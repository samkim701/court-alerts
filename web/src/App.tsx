import { useState } from 'react'
import { RunsPanel } from './components/RunsPanel'
import { OpeningsPanel } from './components/OpeningsPanel'
import './App.css'

type Tab = 'runs' | 'openings'

export default function App() {
  const [tab, setTab] = useState<Tab>('runs')

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>court-alerts</h1>
          <p className="subtitle">Life Time Centreville · read-only monitor</p>
        </div>
      </header>

      <nav className="tabs">
        <button
          className={tab === 'runs' ? 'tab active' : 'tab'}
          onClick={() => setTab('runs')}
        >
          Poll history
        </button>
        <button
          className={tab === 'openings' ? 'tab active' : 'tab'}
          onClick={() => setTab('openings')}
        >
          Openings
        </button>
      </nav>

      <main>
        {tab === 'runs' ? <RunsPanel /> : <OpeningsPanel />}
      </main>
    </div>
  )
}