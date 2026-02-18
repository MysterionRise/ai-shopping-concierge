import { useState } from 'react'
import { Package, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import { ProductCard as ProductCardType } from '../../types'
import SafetyBadge from './SafetyBadge'

interface ProductCardProps {
  product: ProductCardType
}

export default function ProductCard({ product }: ProductCardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className="bg-white rounded-xl border border-gray-200 p-3 hover:shadow-md transition-all cursor-pointer min-w-[220px] max-w-[280px] flex-shrink-0"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex gap-3">
        {product.imageUrl ? (
          <img
            src={product.imageUrl}
            alt={product.name}
            className="w-14 h-14 object-cover rounded-lg flex-shrink-0"
          />
        ) : (
          <div className="w-14 h-14 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
            <Package className="w-6 h-6 text-gray-400" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 text-sm leading-tight line-clamp-2">
            {product.name}
          </h3>
          {product.brand && (
            <p className="text-xs text-gray-500 mt-0.5">{product.brand}</p>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between mt-2">
        <SafetyBadge score={product.safetyScore} badge={product.safetyBadge} />
        {expanded ? (
          <ChevronUp className="w-3.5 h-3.5 text-gray-400" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
        )}
      </div>

      {product.fitReason && !expanded && (
        <p className="text-xs text-primary-600 mt-1.5 line-clamp-1">{product.fitReason}</p>
      )}

      {expanded && (
        <div className="mt-2 pt-2 border-t border-gray-100 space-y-2">
          {product.fitReasons && product.fitReasons.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-600 mb-1">Why this product:</p>
              <ul className="space-y-0.5">
                {product.fitReasons.map((reason, i) => (
                  <li key={i} className="text-xs text-primary-600">
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {product.ingredients.length > 0 ? (
            <div>
              <p className="text-xs font-medium text-gray-600 mb-1">Key ingredients:</p>
              <p className="text-xs text-gray-500">
                {product.ingredients.join(', ')}
              </p>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-yellow-600">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Ingredient list unavailable — safety check not possible</span>
            </div>
          )}

          {product.categories && product.categories.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-600 mb-1">Categories:</p>
              <div className="flex flex-wrap gap-1">
                {product.categories.slice(0, 4).map((cat) => (
                  <span
                    key={cat}
                    className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded"
                  >
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          )}

          {product.dataCompleteness !== undefined && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-400">
                Data completeness: {Math.round(product.dataCompleteness * 100)}%
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
