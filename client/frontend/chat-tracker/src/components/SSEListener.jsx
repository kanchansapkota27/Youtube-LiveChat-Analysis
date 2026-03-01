/**
 * SSEListener — generic per-session SSE subscriber.
 * Props:
 *   sessionId  : string  — session to subscribe to
 *   onMessage  : (msg) => void — callback for each new message
 *   onViewerUpdate : (count, isLive) => void — optional
 */
import { useEffect } from 'react'

const SSEListener = ({ sessionId, onMessage, onViewerUpdate }) => {
  useEffect(() => {
    if (!sessionId) return
    const es = new EventSource(`http://localhost:3000/stream/${sessionId}`)

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (onMessage) onMessage(data)
        if (onViewerUpdate) onViewerUpdate(data?.viewers_count, data?.is_live)
      } catch (e) {
        console.error('SSE parse error:', e)
      }
    }

    es.onerror = (e) => console.error('SSE error:', e)

    return () => es.close()
  }, [sessionId])

  return null
}

export default SSEListener
