import ReactMarkdown from 'react-markdown'
import { ChatMessage } from '../../types'
import ProductCard from '../products/ProductCard'

interface MessageBubbleProps {
  message: ChatMessage
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-primary-500 text-white'
            : 'bg-white border border-gray-200 text-gray-800'
        }`}
      >
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
      </div>
    </div>
  )
}
