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
  overConfidence: number
  safetyBypass: number
  salesPressure: number
}

export interface PersonaEntry {
  conversationId: string
  messageId: string
  scores: PersonaScores
  timestamp: string
}

export interface ChatResponse {
  response: string
  conversationId: string
  intent: string
  safetyViolations: SafetyViolation[]
  productCount: number
}
