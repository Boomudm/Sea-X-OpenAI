export type InvestigationStatus = 'To review' | 'In progress' | 'Resolved'
export type RiskLevel = 'Critical' | 'High' | 'Medium' | 'Low'
export type DecisionType = 'Shortfall confirmed' | 'Not confirmed' | 'Need more information'

export interface AIFinding {
  label: string
  result: 'Match' | 'Warning' | 'Mismatch'
  detail: string
  confidence: number
}

export interface Listing {
  id: string
  title: string
  sku: string
  category: string
  price: number
  previousPrice?: number
  marketPriceMin?: number
  marketPriceMax?: number
  listingUrl?: string
  referenceUrl?: string
  advertisedImage: string
  receivedImage: string
  discrepancy: string
  findings: AIFinding[]
}

export interface BuyerReport {
  id: string
  buyerName: string
  reportedAt: string
  listingId: string
  complaint: string
  attachedImages: number
  evidenceStatus: 'Verified' | 'Pending' | 'Insufficient'
}

export interface Decision {
  sellerId: string
  listingId?: string
  type: DecisionType
  notes: string
  reviewer: string
  timestamp: string
  flagDecisions?: Record<string, 'accepted' | 'dismissed'>
}

export interface NewCaseInput {
  sellerName: string
  listingUrls: string[]
  referenceUrls: string[]
  complaint: string
  currentPrice?: number
  previousPrice?: number
  buyerPhotoCount: number
}

export interface Seller {
  id: string
  name: string
  shopId: string
  initials: string
  recommendation: DecisionType
  riskScore: number
  confidence: number
  keySignal: string
  status: InvestigationStatus
  lastUpdated: string
  createdAt: string
  listingsCount: number
  category: string
  fulfillment: string
  previousInvestigations: number
  summary: string
  listings: Listing[]
  reports: BuyerReport[]
  submittedEvidence?: { photoCount: number; currentPrice?: number }
}
