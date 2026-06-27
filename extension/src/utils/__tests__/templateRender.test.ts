import { describe, it, expect } from 'vitest'
import { renderTemplate } from '../templateRender'

describe('renderTemplate', () => {
  const person = {
    name: 'John Doe',
    company: 'Google',
    role: 'Software Engineer',
  }

  it('renders first_name variable', () => {
    const result = renderTemplate('Hi {{first_name}}!', person)
    expect(result).toBe('Hi John!')
  })

  it('renders name variable', () => {
    const result = renderTemplate('Hello {{name}}', person)
    expect(result).toBe('Hello John Doe')
  })

  it('renders company variable', () => {
    const result = renderTemplate('Works at {{company}}', person)
    expect(result).toBe('Works at Google')
  })

  it('renders role variable', () => {
    const result = renderTemplate('Role: {{role}}', person)
    expect(result).toBe('Role: Software Engineer')
  })

  it('renders multiple variables', () => {
    const result = renderTemplate('{{name}} at {{company}}', person)
    expect(result).toBe('John Doe at Google')
  })

  it('handles missing variables gracefully', () => {
    const result = renderTemplate('Hi {{first_name}}, {{missing}}', person)
    expect(result).toBe('Hi John, ')
  })
})
