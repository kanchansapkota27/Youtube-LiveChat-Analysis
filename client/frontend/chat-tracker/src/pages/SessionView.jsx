import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactPlayer from 'react-player'
import Avatar from 'react-avatar'
import axios from 'axios'
import ChatPanel from '../components/ChatPanel'

const API = 'http://localhost:3000'

export default function SessionView() {
  const { id: sessionId } = useParams()
  const navigate = useNavigate()
  const [session, setSession] = useState(null)
  const [viewerCount, setViewerCount] = useState(0)
  const [isLive, setIsLive] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchSession() {
      try {
        const { data } = await axios.get(`${API}/sessions/${sessionId}`)
        setSession(data)
        setIsLive(data.status === 'active')
      } catch (e) {
        console.error('Session fetch failed:', e)
      } finally {
        setLoading(false)
      }
    }
    fetchSession()
  }, [sessionId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-900 text-gray-400">
        Loading session...
      </div>
    )
  }

  if (!session) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-gray-400 gap-4">
        <p>Session not found.</p>
        <button onClick={() => navigate('/')} className="text-blue-400 hover:underline">
          Back to dashboard
        </button>
      </div>
    )
  }

  const embedUrl = session.video_id
    ? `https://www.youtube.com/embed/${session.video_id}`
    : session.video_url

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Top bar */}
      <header className="flex items-center gap-3 px-4 py-3 bg-gray-800 border-b border-gray-700 shrink-0">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-1 text-gray-400 hover:text-white transition-colors text-sm"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Dashboard
        </button>
        <span className="text-gray-600">|</span>
        <span className="text-sm text-gray-300 truncate">{session.video_title || 'Session'}</span>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left — video player */}
        <div className="flex flex-col flex-1 overflow-hidden p-4 gap-3">
          <div className="w-full aspect-video bg-black rounded-xl overflow-hidden">
            <ReactPlayer
              url={embedUrl}
              width="100%"
              height="100%"
              controls
            />
          </div>

          {/* Video meta */}
          <div className="space-y-1">
            <h2 className="text-base font-semibold leading-snug">
              {session.video_title || 'Loading...'}
            </h2>
            {session.channel_name && (
              <div className="flex items-center gap-2">
                <Avatar name={session.channel_name} round size="24" />
                <span className="text-sm text-gray-300">{session.channel_name}</span>
              </div>
            )}
          </div>
        </div>

        {/* Right — chat panel */}
        <div className="w-80 shrink-0 flex flex-col border-l border-gray-700 bg-gray-800">
          <ChatPanel
            sessionId={sessionId}
            lastCheckpoint={session.last_checkpoint}
            viewerCount={viewerCount}
            isLive={isLive}
            onViewerUpdate={({ viewerCount: vc, isLive: live }) => {
              setViewerCount(vc)
              setIsLive(live)
            }}
          />
        </div>
      </div>
    </div>
  )
}
