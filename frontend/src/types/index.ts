export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  agentName?: string
  products?: ProductCard[]
  safetyViolations?: SafetyViolation[]
  timestamp: string
}

export interface ProductCard {
  id: string
  name: string
  brand: string | null
  ingredients: string[]
  safetyScore: number | null
  imageUrl: string | null
  fitReason?: string
  fitReasons?: string[]
  safetyBadge?: 'safe' | 'unverified'
  categories?: string[]
  dataCompleteness?: number
}

export interface SafetyViolation {
  product: string
  matches?: Array<{ ingredient: string; allergen: string; match_type: string }>
  reason?: string
  gate: string
}

export interface User {
  id: string
  displayName: string
  skinType: string | null
  skinConcerns: string[]
  allergies: string[]
  preferences: Record<string, unknown>
  memoryEnabled: boolean
}

export interface Memory {
  id: string
  content: string
  category: string
  metadata: Record<string, unknown>
  createdAt: string
}

export interface PersonaScores {
  sycophancy: number
  hallucination: number
  over_confidence: number
  safety_bypass: number
  sales_pressure: number
}

export interface PersonaEntry {
  conversation_id: string
  message_id: string
  scores: PersonaScores
  timestamp: string
}

export interface ChatResponse {
  response: string
  conversation_id: string
  intent: string
  safety_violations: SafetyViolation[]
  product_count: number
  products: Record<string, unknown>[]
}
