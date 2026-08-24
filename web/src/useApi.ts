import { useEffect, useState } from 'react'

interface ApiState<T> {
  data: T | null
  error: string | null
  loading: boolean
}

export function useApi<T>(load: () => Promise<T>): ApiState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true

    load()
      .then((result) => {
        if (active) {
          setData(result)
          setError(null)
        }
      })
      .catch((err: Error) => {
        if (active) {
          setError(err.message)
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [])

  return { data, error, loading }
}