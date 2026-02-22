import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { ShieldAlert, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'
import { ChatMessage } from '../../types'
import ProductCard from '../products/ProductCard'

interface MessageBubbleProps {
  message: ChatMessage
}

const INTENT_LABELS: Record<string, { label: string; color: string }> = {
  product_search: { label: 'Product Search', color: 'bg-blue-50 text-blue-600 border-blue-200' },
  ingredient_check: { label: 'Ingredient Check', color: 'bg-emerald-50 text-emerald-600 border-emerald-200' },
  routine_advice: { label: 'Routine Advice', color: 'bg-violet-50 text-violet-600 border-violet-200' },
  general_chat: { label: 'General', color: 'bg-gray-50 text-gray-500 border-gray-200' },
  memory_query: { label: 'Memory', color: 'bg-purple-50 text-purple-600 border-purple-200' },
  safety_override_blocked: { label: 'Safety Block', color: 'bg-red-50 text-red-600 border-red-200' },
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const [showViolations, setShowViolations] = useState(false)

  const violations = message.safetyViolations || []
  const intentInfo = message.intent ? INTENT_LABELS[message.intent] : null

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-message-in`}>
      {!isUser && (
        <div className="flex-shrink-0 mr-2 mt-1">
          <div className="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center">
            <Sparkles className="w-3.5 h-3.5 text-primary-500" />
          </div>
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-primary-500 text-white'
            : 'bg-white border border-gray-200 text-gray-800'
        }`}
      >
        {!isUser && intentInfo && intentInfo.label !== 'General' && (
          <span
            className={`inline-block mb-2 px-2 py-0.5 rounded text-[10px] font-medium border ${intentInfo.color}`}
          >
            {intentInfo.label}
          </span>
        )}
        {isUser ? (
          <p className="text-sm">{message.content}</p>
        ) : (
          <div className="text-sm prose prose-sm max-w-none">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
        {!isUser && message.products && message.products.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1">
              {message.products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </div>
        )}
        {!isUser && violations.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <button
              onClick={() => setShowViolations(!showViolations)}
              className="flex items-center gap-1.5 text-xs text-red-600 hover:text-red-700 transition-colors"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span className="font-medium">
                {violations.length} product{violations.length !== 1 ? 's' : ''} excluded for safety
              </span>
              {showViolations ? (
                <ChevronUp className="w-3 h-3" />
              ) : (
                <ChevronDown className="w-3 h-3" />
              )}
            </button>
            {showViolations && (
              <div className="mt-2 space-y-1.5">
                {violations.map((v, i) => (
                  <div
                    key={i}
                    className="px-2.5 py-1.5 rounded bg-red-50 border border-red-100"
                  >
                    <p className="text-xs font-medium text-red-700">
                      {v.product}
                    </p>
                    {v.matches && v.matches.length > 0 && (
                      <p className="text-[10px] text-red-500 mt-0.5">
                        {v.matches.map((m) => `${m.ingredient} (${m.allergen})`).join(', ')}
                      </p>
                    )}
                    {v.reason && (
                      <p className="text-[10px] text-red-500 mt-0.5">{v.reason}</p>
                    )}
                    <p className="text-[10px] text-red-400 mt-0.5">
                      Gate: {v.gate}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      {isUser && (
        <div className="flex-shrink-0 ml-2 mt-1">
          <div className="w-7 h-7 rounded-full bg-primary-500 flex items-center justify-center">
            <span className="text-[10px] font-semibold text-white">You</span>
          </div>
        </div>
      )}
    </div>
  )
}
