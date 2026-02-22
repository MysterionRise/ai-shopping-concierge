import { useEffect, useRef } from 'react'
import { Info, Sparkles, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ChatMessage, ProductCard } from '../../types'
import MessageBubble from './MessageBubble'
import ProductCardComponent from '../products/ProductCard'
import { usePersonaStore } from '../../stores/personaStore'
import { useUserStore } from '../../stores/userStore'

const STARTER_QUESTIONS = [
  'Recommend a moisturizer for oily skin',
  'Is retinol safe for sensitive skin?',
  'Help me build a morning skincare routine',
]

interface MessageListProps {
  messages: ChatMessage[]
  isTyping: boolean
  streamingContent: string
  streamingProducts: ProductCard[]
  onSend?: (message: string) => void
}

export default function MessageList({
  messages,
  isTyping,
  streamingContent,
  streamingProducts,
  onSend,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const disclaimers = usePersonaStore((s) => s.disclaimers)
  const user = useUserStore((s) => s.user)
  const hasAllergies = user && user.allergies && user.allergies.length > 0

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="max-w-3xl mx-auto">
        {messages.length === 0 && (
          <div className="text-center py-16">
            <Sparkles className="w-10 h-10 text-primary-400 mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-gray-800 mb-2">
              Welcome to Beauty Concierge
            </h2>
            <p className="text-gray-500 mb-8">
              Your AI skincare advisor with built-in safety checks.
              <br />
              Ask about products, ingredients, or routines.
            </p>

            {!hasAllergies && (
              <Link
                to="/profile"
                className="inline-flex items-center gap-2 px-4 py-2 mb-6 rounded-lg bg-amber-50 border border-amber-200 text-amber-700 text-sm hover:bg-amber-100 transition-colors"
              >
                Set up your allergies in your profile for safer recommendations
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            )}

            <div className="flex flex-wrap justify-center gap-2 mt-2">
              {STARTER_QUESTIONS.map((question) => (
                <button
                  key={question}
                  onClick={() => onSend?.(question)}
                  disabled={isTyping}
                  className="px-4 py-2.5 rounded-xl border border-primary-200 bg-white text-sm text-gray-700 hover:bg-primary-50 hover:border-primary-300 hover:text-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id}>
            <MessageBubble message={msg} />
            {msg.role === 'assistant' && disclaimers[msg.id] && (
              <div className="flex justify-start mb-4 ml-2">
                <div className="flex items-start gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg max-w-[80%]">
                  <Info className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-amber-700">{disclaimers[msg.id]}</p>
                </div>
              </div>
            )}
          </div>
        ))}
        {isTyping && streamingContent && (
          <div className="flex justify-start mb-4">
            <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white border border-gray-200 text-gray-800">
              <p className="text-sm">{streamingContent}</p>
              {streamingProducts.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
                    {streamingProducts.map((product) => (
                      <ProductCardComponent key={product.id} product={product} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        {isTyping && !streamingContent && (
          <div className="flex justify-start mb-4">
            <div className="rounded-2xl px-4 py-3 bg-white border border-gray-200">
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0.15s]" />
                <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce [animation-delay:0.3s]" />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
