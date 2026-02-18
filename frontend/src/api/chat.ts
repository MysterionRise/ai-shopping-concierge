import { ChatResponse, ProductCard } from '../types'
import { apiFetch, apiStreamUrl } from './client'

export async function sendMessage(
  message: string,
  userId: string,
  conversationId?: string,
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      user_id: userId,
      conversation_id: conversationId,
    }),
  })
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function parseBackendProduct(p: any): ProductCard {
  return {
    id: p.id,
    name: p.name,
    brand: p.brand || null,
    ingredients: p.key_ingredients || p.ingredients || [],
    safetyScore: p.safety_score ?? null,
    imageUrl: p.image_url || null,
    fitReason: p.fit_reasons?.[0],
    fitReasons: p.fit_reasons || [],
    safetyBadge: p.safety_badge || undefined,
    categories: p.categories || [],
    dataCompleteness: p.data_completeness,
  }
}

export function createSSEConnection(
  message: string,
  userId: string,
  conversationId: string | undefined,
  onToken: (token: string) => void,
  onDone: (conversationId: string) => void,
  onError: (error: string) => void,
  onProducts?: (products: ProductCard[]) => void,
): AbortController {
  const controller = new AbortController()

  fetch(apiStreamUrl('/chat/stream'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      user_id: userId,
      conversation_id: conversationId,
    }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        onError(`Server error: ${response.status} ${response.statusText}`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        onError('No response body')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

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
              if (data.type === 'token') onToken(data.content)
              else if (data.type === 'products' && onProducts) {
                const products = (data.products || []).map(parseBackendProduct)
                onProducts(products)
              } else if (data.type === 'done') onDone(data.conversation_id || '')
              else if (data.type === 'error') onError(data.content)
            } catch {
              // Skip malformed SSE data
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name === 'AbortError') return
      if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
        onError('Connection lost. Please check your network and try again.')
      } else {
        onError(err.message)
      }
    })

  return controller
}
