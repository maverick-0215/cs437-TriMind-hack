// Shapes returned by the Django API (backend/lostfound/serializers.py).

// Keep in sync with Category in backend/lostfound/models.py.
export const CATEGORIES = [
  'Electronics',
  'ID card',
  'Wallet',
  'Keys',
  'Bottle',
  'Bag',
  'Umbrella',
  'Clothing',
  'Books & stationery',
  'Cycle',
  'Jewellery & watches',
  'Other',
]

export type User = {
  email: string
  name: string
  is_admin: boolean
  unread_notifications: number
}

export type PublicItem = {
  id: number
  category: string
  title: string
  date_found: string
  general_area: string
}

export type ItemStatus = 'AVAILABLE' | 'CLAIMED' | 'RETURNED'
export type ClaimStatus = 'PENDING' | 'APPROVED' | 'REJECTED'

export type AdminItem = PublicItem & {
  exact_location: string
  description: string
  has_photo: boolean
  status: ItemStatus
  added_by: string
  created_at: string
}

export type Report = {
  id: number
  category: string
  title: string
  date_lost: string
  place_lost: string
  private_details: string
  linked_item: PublicItem | null
  created_at: string
}

export type AdminReport = Omit<Report, 'linked_item' | 'created_at'> & {
  student: string
  linked_item: number | null
}

export type MyClaim = {
  id: number
  item: PublicItem
  status: ClaimStatus
  created_at: string
  pickup_code: string | null
  code_used_at: string | null
}

export type AdminClaim = {
  id: number
  item: PublicItem
  student: string
  description: string
  status: ClaimStatus
  created_at: string
}

export type Notification = {
  id: number
  message: string
  link: string
  is_read: boolean
  created_at: string
}

export type Handover = {
  id: number
  item: PublicItem
  student: string
  admin: string
  handed_over_at: string
}

export type AdminItemDetail = {
  item: AdminItem
  claims: AdminClaim[]
  awaiting_pickup_by: string | null
  handover: Handover | null
  suggestions: AdminReport[]
  linked_reports: AdminReport[]
  link_options: AdminReport[]
}
