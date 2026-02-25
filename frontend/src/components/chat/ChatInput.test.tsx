import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ChatInput from './ChatInput'

function renderChatInput(props: Partial<Parameters<typeof ChatInput>[0]> = {}) {
  const defaultProps = {
    onSend: vi.fn(),
    disabled: false,
    ...props,
  }
  return { ...render(<ChatInput {...defaultProps} />), onSend: defaultProps.onSend }
}

describe('ChatInput', () => {
  it('renders the textarea with placeholder', () => {
    renderChatInput()
    expect(
      screen.getByPlaceholderText('Ask about skincare products, ingredients, or routines...'),
    ).toBeInTheDocument()
  })

  it('renders the send button', () => {
    renderChatInput()
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBe(1)
  })

  it('updates textarea value on typing', () => {
    renderChatInput()
    const textarea = screen.getByPlaceholderText(
      'Ask about skincare products, ingredients, or routines...',
    )
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    expect(textarea).toHaveValue('Hello')
  })

  it('calls onSend and clears input on send button click', () => {
    const { onSend } = renderChatInput()
    const textarea = screen.getByPlaceholderText(
      'Ask about skincare products, ingredients, or routines...',
    )
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    const sendButton = screen.getByRole('button')
    fireEvent.click(sendButton)
    expect(onSend).toHaveBeenCalledWith('Test message')
    expect(textarea).toHaveValue('')
  })

  it('calls onSend on Enter key press', () => {
    const { onSend } = renderChatInput()
    const textarea = screen.getByPlaceholderText(
      'Ask about skincare products, ingredients, or routines...',
    )
    fireEvent.change(textarea, { target: { value: 'Enter test' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect(onSend).toHaveBeenCalledWith('Enter test')
    expect(textarea).toHaveValue('')
  })

  it('does not send on Shift+Enter', () => {
    const { onSend } = renderChatInput()
    const textarea = screen.getByPlaceholderText(
      'Ask about skincare products, ingredients, or routines...',
    )
    fireEvent.change(textarea, { target: { value: 'Multiline' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('does not send empty or whitespace-only messages', () => {
    const { onSend } = renderChatInput()
    const textarea = screen.getByPlaceholderText(
      'Ask about skincare products, ingredients, or routines...',
    )
    fireEvent.change(textarea, { target: { value: '   ' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('trims whitespace from message before sending', () => {
    const { onSend } = renderChatInput()
    const textarea = screen.getByPlaceholderText(
      'Ask about skincare products, ingredients, or routines...',
    )
    fireEvent.change(textarea, { target: { value: '  Hello world  ' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect(onSend).toHaveBeenCalledWith('Hello world')
  })

  it('disables textarea when disabled prop is true', () => {
    renderChatInput({ disabled: true })
    const textarea = screen.getByPlaceholderText(
      'Ask about skincare products, ingredients, or routines...',
    )
    expect(textarea).toBeDisabled()
  })

  it('disables send button when disabled prop is true', () => {
    renderChatInput({ disabled: true })
    const sendButton = screen.getByRole('button')
    expect(sendButton).toBeDisabled()
  })

  it('disables send button when input is empty', () => {
    renderChatInput()
    const sendButton = screen.getByRole('button')
    expect(sendButton).toBeDisabled()
  })

  it('does not call onSend when disabled even with text', () => {
    const { onSend } = renderChatInput({ disabled: true })
    const textarea = screen.getByPlaceholderText(
      'Ask about skincare products, ingredients, or routines...',
    )
    fireEvent.change(textarea, { target: { value: 'Should not send' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect(onSend).not.toHaveBeenCalled()
  })
})
