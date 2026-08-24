import type { Opening, Run, Subscription } from './types'

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`${path} returned HTTP ${response.status}`)
  }
  return (await response.json()) as T
}

export function fetchRuns(): Promise<Run[]> {
  return getJson<Run[]>('/api/runs')
}

export function fetchOpenings(): Promise<Opening[]> {
  return getJson<Opening[]>('/api/openings')
}

export function fetchSubscriptions(): Promise<Subscription[]> {
  return getJson<Subscription[]>('/api/subscriptions')
}