export interface Tag {
  id: string
  workspace_id: string
  name: string
  color: string | null
}

export interface Person {
  id: string
  workspace_id: string
  name: string
  first_name: string | null
  last_name: string | null
  linkedin_url: string
  linkedin_slug: string
  role: string | null
  company: string | null
  location: string | null
  email: string | null
  phone_number: string | null
  premium: boolean | null
  company_website: string | null
  processed_at: string | null
  processed_at_millis: number | null
  invite_accepted_at: string | null
  invite_accepted_at_millis: number | null
  is_favorite: boolean
  favorite_notes: string | null
  priority: string
  stage: string
  status: string
  next_action_type: string | null
  next_action_date: string | null
  last_action_type: string | null
  last_action_date: string | null
  connection_note: string | null
  notes: string | null
  tags: Tag[]
  created_at: string
  updated_at: string
}
