import type { Decision, InvestigationStatus, Seller } from '../types'
import { publicText, type PipelineCase, type PipelinePriority, type PipelineSignal } from './pipelineCases'
import sampleCases from './sampleCases.json'

export const priorities = {
  red: { label: 'Red', hint: 'Review first', color: '#df553e', tone: 'red', rank: 0 },
  yellow: { label: 'Yellow', hint: 'Check manually', color: '#e7ad49', tone: 'yellow', rank: 1 },
  unknown: { label: 'Needs evidence', hint: 'Insufficient data', color: '#99908b', tone: 'neutral', rank: 2 },
  green: { label: 'Green', hint: 'No flags found', color: '#4d9876', tone: 'green', rank: 3 },
} as const

export type ReviewPriority = PipelinePriority
export type ReviewSignal = PipelineSignal
export type CaseSource = 'captured' | 'sample'
export const scoredPriorities = ['red', 'yellow', 'green'] as const

export const confidenceBands = {
  low: { label: 'Low', range: '0–59%', min: 0, max: 59 },
  medium: { label: 'Medium', range: '60–79%', min: 60, max: 79 },
  high: { label: 'High', range: '80–100%', min: 80, max: 100 },
} as const
export type ConfidenceBand = keyof typeof confidenceBands
export const bandIds = ['low', 'medium', 'high'] as const

export const signals = {
  unsupported: { label: 'Unsupported capacity' },
  capacity: { label: 'Measured capacity shortfall' },
  price: { label: 'Price anomaly' },
  reports: { label: 'Manual checks' },
  clear: { label: 'No flags found' },
} as const satisfies Record<ReviewSignal, { label: string }>
export const signalIds = ['unsupported', 'capacity', 'price', 'reports', 'clear'] as const

export interface ReviewFinding {
  signal: ReviewSignal
  confidence: number
}

export interface ReviewCase {
  id: string
  caseLabel: string
  sellerId: string
  listingId?: string
  shopId?: string
  sellerName?: string
  title: string
  variant?: string
  priority: ReviewPriority
  confidence: number | null
  findings: ReviewFinding[]
  source: CaseSource | 'submitted'
  pipeline?: PipelineCase
  status: InvestigationStatus
  decision?: Decision
  capture?: {
    listingUrl?: string
    referenceUrl?: string
    previousPrice?: number
    currentPrice?: number
    complaint?: string
    photoCount?: number
  }
}

function reviewStatus(decision?: Decision): InvestigationStatus {
  if (!decision) return 'To review'
  return decision.type === 'Need more information' ? 'In progress' : 'Resolved'
}

function pipelineCases(cases: PipelineCase[], decisions: Decision[], source: CaseSource): ReviewCase[] {
  const listingPositions = new Map<string, number>()
  return cases.map((record) => {
    const id = JSON.stringify([source, record.listing_id, record.option_id])
    const decision = decisions.find((item) => item.sellerId === id && item.listingId === record.listing_id)
    if (!listingPositions.has(record.listing_id)) listingPositions.set(record.listing_id, listingPositions.size + 1)
    const sampleShop = 'Sample shop ' + String(listingPositions.get(record.listing_id)).padStart(2, '0')
    return {
      id, sellerId: id, listingId: record.listing_id,
      caseLabel: publicText(record.listing_id),
      sellerName: source === 'sample' ? sampleShop : undefined,
      title: publicText(record.title ?? ('Listing ' + record.listing_id)),
      variant: publicText(record.variation_label ?? record.option_id),
      priority: record.priority,
      confidence: record.confidence,
      findings: record.findings.map((signal) => ({ signal, confidence: record.confidence })),
      pipeline: record,
      source,
      status: reviewStatus(decision),
      decision,
      capture: {
        listingUrl: record.capture.listing_url,
        previousPrice: record.capture.was_thb ?? undefined,
        currentPrice: record.capture.now_thb,
        photoCount: record.capture.photo_count,
      },
    }
  })
}

function submittedCases(sellers: Seller[], decisions: Decision[]): ReviewCase[] {
  return sellers.filter((seller) => seller.id.startsWith('seller-new-')).flatMap((seller) =>
    seller.listings.map((listing, index): ReviewCase => {
      const decision = decisions.find((result) => result.sellerId === seller.id && result.listingId === listing.id)
        ?? decisions.find((result) => result.sellerId === seller.id && !result.listingId)
      const captured = seller.submittedEvidence
      const complaint = seller.reports.find((report) => report.listingId === listing.id)?.complaint
      return {
        id: listing.id, caseLabel: listing.id, sellerId: seller.id, listingId: listing.id, shopId: seller.shopId,
        title: 'Listing link ' + (index + 1),
        sellerName: publicText(seller.name), priority: 'unknown', confidence: null,
        findings: [], source: 'submitted', decision, status: reviewStatus(decision),
        capture: {
          listingUrl: listing.listingUrl,
          referenceUrl: captured ? listing.referenceUrl : undefined,
          currentPrice: index === 0 ? captured?.currentPrice : undefined,
          previousPrice: captured ? listing.previousPrice : undefined,
          complaint: complaint === 'Buyer evidence was submitted with the captured listing sources.' ? undefined : complaint,
          photoCount: index === 0 ? captured?.photoCount : undefined,
        },
      }
    }))
}

export function buildReviewCases(
  sellers: Seller[], decisions: Decision[], captured: PipelineCase[], source: CaseSource,
): ReviewCase[] {
  const cases = source === 'sample'
    ? pipelineCases(sampleCases as PipelineCase[], decisions, source)
    : [...pipelineCases(captured, decisions, source), ...submittedCases(sellers, decisions)]
  // Array sorting preserves the pipeline order for equal-priority, equal-score options.
  return cases.sort((a, b) => priorities[a.priority].rank - priorities[b.priority].rank ||
    (a.priority === 'green' ? 1 : -1) * ((a.confidence ?? -1) - (b.confidence ?? -1)))
}

export function inConfidenceBand(score: number, band: ConfidenceBand) {
  const { min, max } = confidenceBands[band]
  return score >= min && score <= max
}

export function caseVerdict(decision?: Decision) {
  return decision?.type === 'Shortfall confirmed' || decision?.type === 'Not confirmed'
    ? decision.type
    : 'Unsure until decided'
}

export function exportableDecisions(cases: ReviewCase[]) {
  return cases.flatMap(({ pipeline, source, decision }) => {
    if (!pipeline || source !== 'captured' || !decision) return []
    const outcome = decision.type === 'Shortfall confirmed'
      ? { verdict: 'mismatch', decision: 'accepted' }
      : decision.type === 'Not confirmed'
        ? { verdict: 'no_mismatch', decision: 'dismissed' }
        : { verdict: 'unsure', decision: 'needs_more_information' }
    return [{
      listing_id: pipeline.listing_id,
      option_id: pipeline.option_id,
      verdict: outcome.verdict,
      reviewer_decision: { decision: outcome.decision, reason: decision.notes, at: decision.timestamp },
    }]
  })
}
