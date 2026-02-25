import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import SkeletonBlock, { SkeletonRows } from './Skeleton'

describe('SkeletonBlock', () => {
  it('renders an animated pulse div', () => {
    const { container } = render(<SkeletonBlock />)
    const skeleton = container.firstChild as HTMLElement
    expect(skeleton.className).toContain('animate-pulse')
    expect(skeleton.className).toContain('bg-gray-200')
  })

  it('accepts custom className', () => {
    const { container } = render(<SkeletonBlock className="h-8 w-32" />)
    const skeleton = container.firstChild as HTMLElement
    expect(skeleton.className).toContain('h-8')
    expect(skeleton.className).toContain('w-32')
  })
})

describe('SkeletonRows', () => {
  it('renders the specified number of rows', () => {
    const { container } = render(<SkeletonRows count={3} />)
    const rows = container.querySelectorAll('.border.border-gray-100')
    expect(rows).toHaveLength(3)
  })

  it('defaults to 4 rows when no count is specified', () => {
    const { container } = render(<SkeletonRows />)
    const rows = container.querySelectorAll('.border.border-gray-100')
    expect(rows).toHaveLength(4)
  })

  it('renders skeleton blocks within each row', () => {
    const { container } = render(<SkeletonRows count={1} />)
    const pulseElements = container.querySelectorAll('.animate-pulse')
    expect(pulseElements.length).toBeGreaterThan(0)
  })
})
