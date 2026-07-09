import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from './Badge'

describe('Badge', () => {
  it('renders with text', () => {
    render(<Badge variant="primary">Active</Badge>)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('applies correct variant styles', () => {
    render(<Badge variant="success">Done</Badge>)
    const badge = screen.getByText('Done')
    expect(badge.className).toContain('bg-green-100')
  })
})

console.debug('[NetworkPilot Module]', 'module.loaded file=frontend/src/components/common/Badge.test.tsx')
