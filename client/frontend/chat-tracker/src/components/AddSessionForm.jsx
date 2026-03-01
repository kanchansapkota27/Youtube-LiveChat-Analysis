import React, { useState } from 'react'
import axios from 'axios'
import { useSession } from '../contexts/SessionContext'

export default function AddSessionForm() {
  const { refreshSessions, API } = useSession()
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    const trimmed = url.trim()
    if (!trimmed) return
    setError(null)
    setLoading(true)
    try {
      await axios.post(`${API}/sessions`, { video_url: trimmed })
      setUrl('')
      await refreshSessions()
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Failed to add session')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full flex flex-col gap-2">
      <div className="flex gap-2">
        <input
          type="url"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="Paste a YouTube live URL..."
          className="flex-1 px-4 py-2 rounded-lg bg-gray-700 border border-gray-600 text-gray-100 placeholder-gray-400 focus:outline-none focus:border-blue-500"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="px-5 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white font-semibold disabled:opacity-50 transition-colors"
        >
          {loading ? 'Adding...' : 'Track'}
        </button>
      </div>
      {error && <p className="text-red-400 text-sm">{error}</p>}
    </form>
  )
}
