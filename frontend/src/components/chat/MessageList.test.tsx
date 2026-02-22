import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import MessageList from './MessageList'

vi.mock('../../stores/personaStore', () => ({
  usePersonaStore: () => ({}),
}))

vi.mock('../../stores/userStore', () => ({
  useUserStore: () => null,
}))

function renderMessageList(props: Partial<Parameters<typeof MessageList>[0]> = {}) {
  const defaultProps = {
    messages: [],
    isTyping: false,
    streamingContent: '',
    streamingProducts: [],
    onSend: vi.fn(),
    ...props,
  }
  return render(
    <MemoryRouter>
      <MessageList {...defaultProps} />
    </MemoryRouter>,
  )
}

describe('MessageList', () => {
  it('renders welcome state when messages are empty', () => {
    renderMessageList()
    expect(screen.getByText('Welcome to Beauty Concierge')).toBeInTheDocument()
    expect(
      screen.getByText(/Your AI skincare advisor with built-in safety checks/),
    ).toBeInTheDocument()
  })

  it('renders starter question chips', () => {
    renderMessageList()
    expect(
      screen.getByText('Recommend a moisturizer for oily skin'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Is retinol safe for sensitive skin?'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('Help me build a morning skincare routine'),
    ).toBeInTheDocument()
  })

  it('calls onSend when a starter chip is clicked', () => {
    const onSend = vi.fn()
    renderMessageList({ onSend })
    fireEvent.click(screen.getByText('Recommend a moisturizer for oily skin'))
    expect(onSend).toHaveBeenCalledWith('Recommend a moisturizer for oily skin')
  })

  it('hides welcome state when messages are present', () => {
    renderMessageList({
      messages: [
        {
          id: '1',
          role: 'user',
          content: 'Hello',
          timestamp: new Date().toISOString(),
        },
      ],
    })
    expect(screen.queryByText('Welcome to Beauty Concierge')).not.toBeInTheDocument()
  })

  it('shows typing indicator when isTyping is true and no streaming content', () => {
    const { container } = renderMessageList({ isTyping: true })
    const bounceDots = container.querySelectorAll('.animate-bounce')
    expect(bounceDots.length).toBe(3)
  })

  it('shows streaming content when isTyping with streamingContent', () => {
    renderMessageList({
      isTyping: true,
      streamingContent: 'I recommend trying...',
    })
    expect(screen.getByText('I recommend trying...')).toBeInTheDocument()
  })
})
