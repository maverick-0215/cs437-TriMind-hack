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
  created_at: string
  // S27: OPEN, APPROVED (waiting for pickup) or CLOSED (collected).
  status: ReportStatus
  closed_at: string | null
  item: PublicItem | null
}

export type ReportStatus = 'OPEN' | 'APPROVED' | 'CLOSED'

/** Badge text and colour class for each report status. */
export const REPORT_STATUS: Record<ReportStatus, { label: string; className: string }> = {
  OPEN: { label: 'Open', className: 'available' },
  APPROVED: { label: 'Ready for pickup', className: 'claimed' },
  CLOSED: { label: 'Closed', className: 'returned' },
}

/** S25: a found item that may match a report, and who to contact about it. */
export type MatchItem = PublicItem & { contact: string; score: number }

export type ReportDetail = Report & {
  matches: MatchItem[]
  security_contact: string
}

export type AdminReport = Omit<Report, 'created_at' | 'status' | 'closed_at' | 'item'> & {
  student: string
}

/** S13: a lost report that matches a found item, for the guard to check in person. */
export type Candidate = AdminReport & { score: number }

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
  candidates: Candidate[]
}

/** S28: permanent admins come from ADMIN_EMAILS in .env; the rest were added in the app. */
export type AdminList = {
  permanent: string[]
  added: { id: number; email: string; added_by: string; created_at: string }[]
}
