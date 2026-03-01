import React, { useEffect, useRef, useState } from 'react'
import VideoMessage from './VideoMessage'

const MAX_LIVE = 150

export default function ChatPanel({ sessionId, lastCheckpoint, viewerCount, isLive, onViewerUpdate }) {
  const [historicalChats, setHistoricalChats] = useState([])
  const [liveChats, setLiveChats] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(true)
  const containerRef = useRef(null)
  const hasResumed = !!lastCheckpoint  // session was paused before → show divider

  // Fetch historical chats on mount
  useEffect(() => {
    async function fetchHistory() {
      try {
        const res = await fetch(`http://localhost:3000/sessions/${sessionId}/chats?limit=500`)
        const data = await res.json()
        setHistoricalChats(data)
      } catch (e) {
        console.error('Failed to fetch history:', e)
      } finally {
        setLoadingHistory(false)
      }
    }
    fetchHistory()
  }, [sessionId])

  // SSE live messages
  useEffect(() => {
    const es = new EventSource(`http://localhost:3000/stream/${sessionId}`)
    es.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        setLiveChats(prev => [...prev, msg].slice(-MAX_LIVE))
        if (onViewerUpdate && msg.viewers_count != null) {
          onViewerUpdate({ viewerCount: msg.viewers_count, isLive: msg.is_live })
        }
      } catch (e) {
        console.error('SSE parse error:', e)
      }
    }
    es.onerror = (e) => console.error('SSE error:', e)
    return () => es.close()
  }, [sessionId])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [liveChats])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700 shrink-0">
        <span className="text-sm font-semibold">Live Chat</span>
        <div className="flex items-center gap-2 text-xs text-gray-300">
          <span className={`h-2 w-2 rounded-full ${isLive ? 'bg-green-400' : 'bg-gray-500'}`} />
          <span className="font-bold">{viewerCount?.toLocaleString() ?? '—'}</span>
          <span>watching</span>
        </div>
      </div>

      {/* Messages */}
      <div ref={containerRef} className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
        {loadingHistory
          ? <p className="text-center text-gray-500 text-xs animate-pulse pt-4">Loading history...</p>
          : historicalChats.map((msg, i) => <VideoMessage key={`h-${i}`} data={msg} />)
        }

        {/* Checkpoint divider — shown when a session was paused and resumed */}
        {!loadingHistory && hasResumed && (liveChats.length > 0 || historicalChats.length > 0) && (
          <div className="flex items-center gap-2 py-2">
            <div className="flex-1 h-px bg-gray-600" />
            <span className="text-xs text-gray-400 whitespace-nowrap">Session resumed</span>
            <div className="flex-1 h-px bg-gray-600" />
          </div>
        )}

        {liveChats.map((msg, i) => <VideoMessage key={`l-${i}`} data={msg} />)}
      </div>

      {/* Disabled input — read-only indicator */}
      <div className="px-3 py-2 border-t border-gray-700 shrink-0">
        <input
          disabled
          type="text"
          placeholder="Unable to send messages from this interface"
          className="w-full px-3 py-1.5 text-xs rounded bg-transparent border border-gray-600 text-gray-500 cursor-not-allowed outline-none"
        />
      </div>
    </div>
  )
}
