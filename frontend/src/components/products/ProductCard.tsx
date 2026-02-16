import { ProductCard as ProductCardType } from '../../types'
import SafetyBadge from './SafetyBadge'

interface ProductCardProps {
  product: ProductCardType
}

export default function ProductCard({ product }: ProductCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex gap-4">
        {product.imageUrl && (
          <img
            src={product.imageUrl}
            alt={product.name}
            className="w-16 h-16 object-cover rounded-lg"
          />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-medium text-gray-900 text-sm truncate">
                {product.name}
              </h3>
              {product.brand && (
                <p className="text-xs text-gray-500">{product.brand}</p>
              )}
            </div>
            <SafetyBadge score={product.safetyScore} />
          </div>
          {product.ingredients.length > 0 && (
            <p className="text-xs text-gray-400 mt-2 truncate">
              {product.ingredients.slice(0, 5).join(', ')}
              {product.ingredients.length > 5 && '...'}
            </p>
          )}
          {product.fitReason && (
            <p className="text-xs text-primary-600 mt-1">{product.fitReason}</p>
          )}
        </div>
      </div>
    </div>
  )
}
