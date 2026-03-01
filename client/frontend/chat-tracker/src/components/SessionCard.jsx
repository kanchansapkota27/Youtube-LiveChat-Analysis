import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import Avatar from 'react-avatar'
import { useSession } from '../contexts/SessionContext'

function StatusDot({ status }) {
  const colors = {
    active: 'bg-green-400',
    paused: 'bg-yellow-400',
    stopped: 'bg-gray-400',
    fetching: 'bg-blue-400 animate-pulse',
  }
  const labels = {
    active: 'Live',
    paused: 'Paused',
    stopped: 'Stopped',
    fetching: 'Fetching info…',
  }
  return (
    <span className="flex items-center gap-1.5 text-xs font-medium">
      <span className={`inline-block h-2 w-2 rounded-full ${colors[status] ?? 'bg-gray-400'}`} />
      {labels[status] ?? status}
    </span>
  )
}

export default function SessionCard({ session }) {
  const { refreshSessions, API } = useSession()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)

  const isFetching = session.status === 'fetching'

  async function apiCall(fn) {
    setBusy(true)
    try { await fn() } finally { setBusy(false); await refreshSessions() }
  }

  function handleCardClick() {
    if (isFetching) return
    navigate(`/session/${session.session_id}`)
  }

  function stopProp(e) { e.stopPropagation() }

  async function handlePause(e) {
    stopProp(e)
    await apiCall(() => axios.put(`${API}/sessions/${session.session_id}/pause`))
  }

  async function handleResume(e) {
    stopProp(e)
    await apiCall(() => axios.put(`${API}/sessions/${session.session_id}/resume`))
  }

  async function handleDelete(e) {
    stopProp(e)
    if (!window.confirm('Delete this session? Chats will be archived.')) return
    await apiCall(() => axios.delete(`${API}/sessions/${session.session_id}`))
  }

  const thumb = session.thumbnail_url
  const title = session.video_title || 'Loading...'
  const channel = session.channel_name || '—'

  return (
    <div
      onClick={handleCardClick}
      className={`flex flex-col bg-gray-700 rounded-xl overflow-hidden shadow-lg transition-all ${
        isFetching
          ? 'cursor-not-allowed opacity-75'
          : 'cursor-pointer hover:ring-2 hover:ring-blue-500'
      }`}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gray-800 overflow-hidden">
        {isFetching
          ? <div className="w-full h-full flex flex-col items-center justify-center gap-3 px-6">
              <div className="h-3 w-full bg-gray-600 rounded animate-pulse" />
              <div className="h-3 w-3/4 bg-gray-600 rounded animate-pulse" />
              <div className="h-3 w-1/2 bg-gray-600 rounded animate-pulse" />
            </div>
          : thumb
            ? <img src={thumb} alt={title} className="w-full h-full object-cover" />
            : <div className="w-full h-full flex items-center justify-center">
                <Avatar name={channel} size="64" round />
              </div>
        }
        <div className="absolute top-2 left-2 bg-gray-900/80 rounded-full px-2 py-0.5">
          <StatusDot status={session.status} />
        </div>
      </div>

      {/* Info */}
      <div className="flex flex-col gap-1 p-3 flex-1">
        {isFetching
          ? <>
              <div className="h-3 w-full bg-gray-600 rounded animate-pulse" />
              <div className="h-3 w-2/3 bg-gray-600 rounded animate-pulse mt-1" />
            </>
          : <>
              <p className="text-white text-sm font-semibold line-clamp-2 leading-snug">{title}</p>
              <p className="text-gray-400 text-xs">{channel}</p>
            </>
        }
      </div>

      {/* Controls */}
      <div className="flex gap-2 px-3 pb-3" onClick={stopProp}>
        {!isFetching && session.status === 'active' && (
          <button
            onClick={handlePause}
            disabled={busy}
            className="flex-1 py-1.5 rounded-lg bg-yellow-600 hover:bg-yellow-500 text-white text-xs font-medium disabled:opacity-50 transition-colors"
          >
            Pause
          </button>
        )}
        {!isFetching && session.status === 'paused' && (
          <button
            onClick={handleResume}
            disabled={busy}
            className="flex-1 py-1.5 rounded-lg bg-green-700 hover:bg-green-600 text-white text-xs font-medium disabled:opacity-50 transition-colors"
          >
            Resume
          </button>
        )}
        <button
          onClick={handleDelete}
          disabled={busy}
          className="flex-1 py-1.5 rounded-lg bg-red-700 hover:bg-red-600 text-white text-xs font-medium disabled:opacity-50 transition-colors"
        >
          Delete
        </button>
      </div>
    </div>
  )
}
