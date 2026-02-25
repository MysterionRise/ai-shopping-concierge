import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ProductCard from './ProductCard'
import { ProductCard as ProductCardType } from '../../types'

function renderProductCard(overrides: Partial<ProductCardType> = {}) {
  const product: ProductCardType = {
    id: 'prod-1',
    name: 'Gentle Moisturizer',
    brand: 'SkinCare Co',
    ingredients: ['hyaluronic acid', 'ceramides', 'niacinamide'],
    safetyScore: 8.5,
    imageUrl: null,
    ...overrides,
  }
  return render(<ProductCard product={product} />)
}

describe('ProductCard', () => {
  it('renders the product name', () => {
    renderProductCard()
    expect(screen.getByText('Gentle Moisturizer')).toBeInTheDocument()
  })

  it('renders the brand name', () => {
    renderProductCard()
    expect(screen.getByText('SkinCare Co')).toBeInTheDocument()
  })

  it('does not render brand when null', () => {
    renderProductCard({ brand: null })
    expect(screen.queryByText('SkinCare Co')).not.toBeInTheDocument()
  })

  it('renders image when imageUrl is provided', () => {
    renderProductCard({ imageUrl: 'https://example.com/img.jpg' })
    const img = screen.getByAltText('Gentle Moisturizer')
    expect(img).toBeInTheDocument()
    expect(img).toHaveAttribute('src', 'https://example.com/img.jpg')
  })

  it('renders placeholder icon when no image', () => {
    const { container } = renderProductCard({ imageUrl: null })
    // The placeholder div has the Package icon
    const placeholders = container.querySelectorAll('.bg-gray-100')
    expect(placeholders.length).toBeGreaterThan(0)
  })

  it('renders safety badge', () => {
    renderProductCard({ safetyScore: 8.5 })
    expect(screen.getByText(/8\.5/)).toBeInTheDocument()
  })

  it('renders unverified badge when score is null', () => {
    renderProductCard({ safetyScore: null })
    expect(screen.getByText(/Unverified/)).toBeInTheDocument()
  })

  it('renders fitReason when not expanded', () => {
    renderProductCard({ fitReason: 'Great for oily skin' })
    expect(screen.getByText('Great for oily skin')).toBeInTheDocument()
  })

  it('expands on click to show ingredients', () => {
    renderProductCard()
    const card = screen.getByText('Gentle Moisturizer').closest('.bg-white')!
    fireEvent.click(card)
    expect(screen.getByText('Key ingredients:')).toBeInTheDocument()
    expect(screen.getByText('hyaluronic acid, ceramides, niacinamide')).toBeInTheDocument()
  })

  it('shows ingredient unavailable warning when expanded with empty ingredients', () => {
    renderProductCard({ ingredients: [] })
    const card = screen.getByText('Gentle Moisturizer').closest('.bg-white')!
    fireEvent.click(card)
    expect(
      screen.getByText('Ingredient list unavailable — safety check not possible'),
    ).toBeInTheDocument()
  })

  it('shows categories when expanded', () => {
    renderProductCard({ categories: ['moisturizer', 'face cream'] })
    const card = screen.getByText('Gentle Moisturizer').closest('.bg-white')!
    fireEvent.click(card)
    expect(screen.getByText('Categories:')).toBeInTheDocument()
    expect(screen.getByText('moisturizer')).toBeInTheDocument()
    expect(screen.getByText('face cream')).toBeInTheDocument()
  })

  it('shows data completeness when expanded', () => {
    renderProductCard({ dataCompleteness: 0.85 })
    const card = screen.getByText('Gentle Moisturizer').closest('.bg-white')!
    fireEvent.click(card)
    expect(screen.getByText('Data completeness: 85%')).toBeInTheDocument()
  })

  it('shows fitReasons when expanded', () => {
    renderProductCard({ fitReasons: ['Good for oily skin', 'Contains niacinamide'] })
    const card = screen.getByText('Gentle Moisturizer').closest('.bg-white')!
    fireEvent.click(card)
    expect(screen.getByText('Why this product:')).toBeInTheDocument()
    expect(screen.getByText('Good for oily skin')).toBeInTheDocument()
    expect(screen.getByText('Contains niacinamide')).toBeInTheDocument()
  })

  it('collapses when clicked again', () => {
    renderProductCard()
    const card = screen.getByText('Gentle Moisturizer').closest('.bg-white')!
    fireEvent.click(card)
    expect(screen.getByText('Key ingredients:')).toBeInTheDocument()
    fireEvent.click(card)
    expect(screen.queryByText('Key ingredients:')).not.toBeInTheDocument()
  })
})
