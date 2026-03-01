import React, { useEffect } from 'react'
import { useSession } from '../contexts/SessionContext'
import SessionCard from '../components/SessionCard'
import AddSessionForm from '../components/AddSessionForm'

export default function Dashboard() {
  const { sessions, refreshSessions, loading, API } = useSession()

  useEffect(() => {
    refreshSessions()
  }, [])

  // Poll every 2 s while any session is still fetching video info
  useEffect(() => {
    const hasFetching = sessions.some(s => s.status === 'fetching')
    if (!hasFetching) return
    const id = setInterval(refreshSessions, 2000)
    return () => clearInterval(id)
  }, [sessions])

  const maxSessions = 3  // matches backend default; could fetch from /config

  const activeSessions = sessions.filter(s => s.status !== 'deleted')

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="flex items-center gap-3 px-6 py-4 bg-gray-800 border-b border-gray-700">
        <img
          src="https://www.cdnlogo.com/logos/y/57/youtube-icon.svg"
          className="w-8 h-8"
          alt="YouTube"
        />
        <h1 className="text-lg font-bold tracking-wide">Live Chat Analyzer</h1>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 flex flex-col gap-8">
        {/* Add session form */}
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            Track a new stream
          </h2>
          <AddSessionForm />
        </section>

        {/* Session grid */}
        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
              Sessions
            </h2>
            <span className="text-xs text-gray-500">
              {activeSessions.length} / {maxSessions}
            </span>
          </div>

          {loading && activeSessions.length === 0 && (
            <p className="text-gray-500 text-sm animate-pulse">Loading sessions...</p>
          )}

          {!loading && activeSessions.length === 0 && (
            <div className="flex items-center justify-center h-48 rounded-xl border-2 border-dashed border-gray-700 text-gray-500">
              No active sessions. Paste a YouTube live URL above to get started.
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeSessions.map(session => (
              <SessionCard key={session.session_id} session={session} />
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
