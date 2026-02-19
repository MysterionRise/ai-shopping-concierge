import { useEffect, useRef } from 'react'
import { personaStreamUrl } from '../api/persona'
import { usePersonaStore } from '../stores/personaStore'

const MAX_RETRIES = 5
const BASE_DELAY_MS = 1000

export function usePersonaStream(conversationId: string | undefined) {
  const updateScores = usePersonaStore((s) => s.updateScores)
  const addDisclaimer = usePersonaStore((s) => s.addDisclaimer)
  const retryCount = useRef(0)
  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (!conversationId) return

    retryCount.current = 0

    function connect() {
      const controller = new AbortController()
      controllerRef.current = controller

      const url = personaStreamUrl(conversationId!)

      fetch(url, { signal: controller.signal })
        .then(async (response) => {
          if (!response.ok || !response.body) return

          const reader = response.body.getReader()
          const decoder = new TextDecoder()
          let buffer = ''

          retryCount.current = 0 // Reset on successful connection

          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6))
                  if (data.scores) {
                    updateScores(data)
                  }
                  if (data.type === 'intervention' && data.message_id) {
                    addDisclaimer(data.message_id, data.text || 'AI confidence notice')
                  }
                } catch {
                  // Skip malformed SSE data
                }
              }
            }
          }

          // Stream ended normally — reconnect
          scheduleReconnect()
        })
        .catch((err) => {
          if (err.name === 'AbortError') return
          scheduleReconnect()
        })
    }

    function scheduleReconnect() {
      if (retryCount.current >= MAX_RETRIES) return

      const delay = BASE_DELAY_MS * Math.pow(2, retryCount.current)
      retryCount.current++
      setTimeout(connect, delay)
    }

    connect()

    return () => {
      controllerRef.current?.abort()
      controllerRef.current = null
    }
  }, [conversationId, updateScores, addDisclaimer])
}
