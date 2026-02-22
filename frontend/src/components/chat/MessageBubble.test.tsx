import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import MessageBubble from './MessageBubble'
import { ChatMessage } from '../../types'

function renderBubble(overrides: Partial<ChatMessage> = {}) {
  const message: ChatMessage = {
    id: 'msg-1',
    role: 'user',
    content: 'Hello there',
    timestamp: new Date().toISOString(),
    ...overrides,
  }
  return render(<MessageBubble message={message} />)
}

describe('MessageBubble', () => {
  it('renders user message content', () => {
    renderBubble({ role: 'user', content: 'What moisturizer should I use?' })
    expect(screen.getByText('What moisturizer should I use?')).toBeInTheDocument()
  })

  it('renders assistant message content', () => {
    renderBubble({ role: 'assistant', content: 'I recommend a gentle moisturizer.' })
    expect(screen.getByText('I recommend a gentle moisturizer.')).toBeInTheDocument()
  })

  it('shows intent badge for non-general assistant messages', () => {
    renderBubble({
      role: 'assistant',
      content: 'Here are some products.',
      intent: 'product_search',
    })
    expect(screen.getByText('Product Search')).toBeInTheDocument()
  })

  it('does not show intent badge for general_chat', () => {
    renderBubble({
      role: 'assistant',
      content: 'Hi!',
      intent: 'general_chat',
    })
    expect(screen.queryByText('General')).not.toBeInTheDocument()
  })

  it('does not show intent badge for user messages', () => {
    renderBubble({
      role: 'user',
      content: 'Search for products',
      intent: 'product_search',
    })
    expect(screen.queryByText('Product Search')).not.toBeInTheDocument()
  })

  it('shows safety violations toggle', () => {
    renderBubble({
      role: 'assistant',
      content: 'Some products were filtered.',
      safetyViolations: [
        {
          product: 'Dangerous Cream',
          gate: 'rule_based',
          matches: [{ ingredient: 'methylparaben', allergen: 'paraben', match_type: 'synonym' }],
        },
      ],
    })
    expect(screen.getByText('1 product excluded for safety')).toBeInTheDocument()
  })

  it('expands safety violation details on click', () => {
    renderBubble({
      role: 'assistant',
      content: 'Filtered.',
      safetyViolations: [
        {
          product: 'Bad Product',
          gate: 'llm',
          reason: 'Contains allergen',
        },
      ],
    })
    fireEvent.click(screen.getByText('1 product excluded for safety'))
    expect(screen.getByText('Bad Product')).toBeInTheDocument()
    expect(screen.getByText('Contains allergen')).toBeInTheDocument()
    expect(screen.getByText('Gate: llm')).toBeInTheDocument()
  })
})
