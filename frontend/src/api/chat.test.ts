import { describe, it, expect } from 'vitest'
import { parseBackendProduct } from './chat'

describe('parseBackendProduct', () => {
  it('parses a full backend product', () => {
    const result = parseBackendProduct({
      id: 'prod-1',
      name: 'Moisturizer',
      brand: 'Brand',
      key_ingredients: ['hyaluronic acid'],
      safety_score: 8.5,
      image_url: 'https://example.com/img.jpg',
      fit_reasons: ['Good for oily skin'],
      safety_badge: 'safe',
      categories: ['face cream'],
      data_completeness: 0.9,
    })
    expect(result).toEqual({
      id: 'prod-1',
      name: 'Moisturizer',
      brand: 'Brand',
      ingredients: ['hyaluronic acid'],
      safetyScore: 8.5,
      imageUrl: 'https://example.com/img.jpg',
      fitReason: 'Good for oily skin',
      fitReasons: ['Good for oily skin'],
      safetyBadge: 'safe',
      categories: ['face cream'],
      dataCompleteness: 0.9,
    })
  })

  it('handles missing optional fields', () => {
    const result = parseBackendProduct({
      id: 'prod-2',
      name: 'Simple Product',
    })
    expect(result.brand).toBeNull()
    expect(result.ingredients).toEqual([])
    expect(result.safetyScore).toBeNull()
    expect(result.imageUrl).toBeNull()
    expect(result.fitReason).toBeUndefined()
    expect(result.fitReasons).toEqual([])
    expect(result.safetyBadge).toBeUndefined()
    expect(result.categories).toEqual([])
  })

  it('falls back to ingredients when key_ingredients is missing', () => {
    const result = parseBackendProduct({
      id: 'prod-3',
      name: 'Product',
      ingredients: ['vitamin c', 'retinol'],
    })
    expect(result.ingredients).toEqual(['vitamin c', 'retinol'])
  })

  it('uses first fit_reason as fitReason', () => {
    const result = parseBackendProduct({
      id: 'prod-4',
      name: 'Product',
      fit_reasons: ['First reason', 'Second reason'],
    })
    expect(result.fitReason).toBe('First reason')
    expect(result.fitReasons).toEqual(['First reason', 'Second reason'])
  })

  it('handles safety_score of 0', () => {
    const result = parseBackendProduct({
      id: 'prod-5',
      name: 'Product',
      safety_score: 0,
    })
    expect(result.safetyScore).toBe(0)
  })
})
