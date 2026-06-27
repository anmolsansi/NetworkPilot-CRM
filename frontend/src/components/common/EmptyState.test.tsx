import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EmptyState } from './EmptyState'

describe('EmptyState', () => {
  it('renders title', () => {
    render(<EmptyState title="No items found" />)
    expect(screen.getByText('No items found')).toBeInTheDocument()
  })

  it('renders description', () => {
    render(
      <EmptyState
        title="No items"
        description="Try adding some items"
      />
    )
    expect(screen.getByText('Try adding some items')).toBeInTheDocument()
  })
})
