import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ChatView from './ChatView'

const mockSendMessage = vi.fn()

vi.mock('../../hooks/useChat', () => ({
  useChat: () => ({
    messages: [],
    isTyping: false,
    streamingContent: '',
    streamingProducts: [],
    sendMessage: mockSendMessage,
  }),
}))

vi.mock('./MessageList', () => ({
  default: ({ messages, isTyping }: { messages: unknown[]; isTyping: boolean }) => (
    <div data-testid="message-list">
      {messages.length === 0 && <span>No messages</span>}
      {isTyping && <span>Typing...</span>}
    </div>
  ),
}))

vi.mock('./ChatInput', () => ({
  default: ({
    onSend,
    disabled,
  }: {
    onSend: (msg: string) => void
    disabled: boolean
  }) => (
    <div data-testid="chat-input">
      <button onClick={() => onSend('test')} disabled={disabled}>
        Send
      </button>
    </div>
  ),
}))

vi.mock('./PersonaSidebar', () => ({
  default: () => <div data-testid="persona-sidebar">Persona Sidebar</div>,
}))

describe('ChatView', () => {
  it('renders the message list', () => {
    render(<ChatView />)
    expect(screen.getByTestId('message-list')).toBeInTheDocument()
  })

  it('renders the chat input', () => {
    render(<ChatView />)
    expect(screen.getByTestId('chat-input')).toBeInTheDocument()
  })

  it('renders the Persona toggle button', () => {
    render(<ChatView />)
    expect(screen.getByTitle('Toggle persona monitor')).toBeInTheDocument()
    expect(screen.getByText('Persona')).toBeInTheDocument()
  })

  it('does not show persona sidebar by default', () => {
    render(<ChatView />)
    expect(screen.queryByTestId('persona-sidebar')).not.toBeInTheDocument()
  })

  it('shows persona sidebar when toggle is clicked', () => {
    render(<ChatView />)
    fireEvent.click(screen.getByTitle('Toggle persona monitor'))
    expect(screen.getByTestId('persona-sidebar')).toBeInTheDocument()
  })

  it('hides persona sidebar when toggle is clicked again', () => {
    render(<ChatView />)
    const toggle = screen.getByTitle('Toggle persona monitor')
    fireEvent.click(toggle)
    expect(screen.getByTestId('persona-sidebar')).toBeInTheDocument()
    fireEvent.click(toggle)
    expect(screen.queryByTestId('persona-sidebar')).not.toBeInTheDocument()
  })

  it('passes sendMessage to child components', () => {
    render(<ChatView />)
    fireEvent.click(screen.getByText('Send'))
    expect(mockSendMessage).toHaveBeenCalledWith('test', true)
  })
})
