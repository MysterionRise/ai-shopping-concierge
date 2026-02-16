import { useQuery } from '@tanstack/react-query'
import { searchProducts } from '../api/products'

export function useProducts(query: string) {
  return useQuery({
    queryKey: ['products', query],
    queryFn: () => searchProducts(query),
    enabled: query.length > 0,
  })
}
