interface PersonData {
  name?: string
  company?: string
  role?: string
}

export function renderTemplate(body: string, person: PersonData): string {
  const firstName = person.name?.split(' ')[0] || ''
  
  return body
    .replace(/\{\{first_name\}\}/g, firstName)
    .replace(/\{\{name\}\}/g, person.name || '')
    .replace(/\{\{company\}\}/g, person.company || '')
    .replace(/\{\{role\}\}/g, person.role || '')
    .replace(/\{\{.*?\}\}/g, '')
}
