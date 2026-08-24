export interface Triage {
  category: string
  needs_human: boolean
  confidence: number
  summary: string
  source: string
  triaged_at: string
}

export interface Run {
  id: number
  started_at: string
  status: string
  slot_count: number
  opened_count: number
  alerts_sent: number
  error_type: string | null
  error_message: string | null
  triage: Triage | null
}

export interface Opening {
  court: string
  start: string
  end: string
}

export interface Subscription {
  label: string
  weekdays: number[]
  earliest_hour: number
  latest_hour: number
  courts: string[] | null
}