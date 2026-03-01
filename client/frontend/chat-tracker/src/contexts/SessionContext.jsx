import React, { createContext, useContext, useState, useCallback } from 'react'
import axios from 'axios'

const API = 'http://localhost:3000'

const SessionContext = createContext()

export function SessionProvider({ children }) {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const refreshSessions = useCallback(async () => {
    try {
      setLoading(true)
      const { data } = await axios.get(`${API}/sessions`)
      setSessions(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  return (
    <SessionContext.Provider value={{ sessions, setSessions, refreshSessions, loading, error, API }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used within a SessionProvider')
  return ctx
}
