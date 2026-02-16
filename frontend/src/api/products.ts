import { ProductCard } from '../types'
import { apiFetch } from './client'

export async function searchProducts(
  query: string,
  limit = 10,
): Promise<ProductCard[]> {
  const data = await apiFetch<Array<Record<string, unknown>>>(
    `/products/search?q=${encodeURIComponent(query)}&limit=${limit}`,
  )
  return data.map((p) => ({
    id: p.id as string,
    name: p.name as string,
    brand: p.brand as string | null,
    ingredients: p.ingredients as string[],
    safetyScore: p.safety_score as number | null,
    imageUrl: p.image_url as string | null,
  }))
}
