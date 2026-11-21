import type { Decision, InvestigationStatus, Seller } from '../types'

export const priorities = {
  red: { label: 'Red', hint: 'Review first', color: '#df553e', tone: 'red', rank: 0 },
  yellow: { label: 'Yellow', hint: 'Check manually', color: '#e7ad49', tone: 'yellow', rank: 1 },
  green: { label: 'Green', hint: 'No flags found', color: '#4d9876', tone: 'green', rank: 2 },
  unknown: { label: 'Needs evidence', hint: 'Insufficient data', color: '#99908b', tone: 'neutral', rank: 3 },
} as const

export type ReviewPriority = keyof typeof priorities
type ScoredPriority = Exclude<ReviewPriority, 'unknown'>
export const scoredPriorities = ['red', 'yellow', 'green'] as const

export const confidenceBands = {
  low: { label: 'Low', range: '0–59%', min: 0, max: 59 },
  medium: { label: 'Medium', range: '60–79%', min: 60, max: 79 },
  high: { label: 'High', range: '80–100%', min: 80, max: 100 },
} as const
export type ConfidenceBand = keyof typeof confidenceBands
export const bandIds = ['low', 'medium', 'high'] as const

export const signals = {
  unsupported: {
    label: 'Unsupported capacity', rule: 'Q2',
    summary: 'The listed capacity is absent from the confirmed capacity list for this model.',
    evidence: ['Listing capture identifies the exact model and advertised capacity.', 'Manufacturer capacity list does not include the advertised option.'],
    source: 'The listing and a manufacturer specification can be matched by model.',
    agreement: 'The model identifiers agree across sources, exposing a capacity discrepancy.',
    next: 'A manufacturer record for an additional regional or newly released variant.',
  },
  capacity: {
    label: 'Measured capacity shortfall', rule: 'Q3',
    summary: 'Buyer tests show less usable storage than the selected option promises.',
    evidence: ['The captured listing identifies the same advertised variant.', 'Two independent buyers report usable capacity below 85% for this variant.'],
    source: 'The listing and buyer tests can be matched to the selected SSD.',
    agreement: 'Independent tests indicate the same capacity shortfall.',
    next: 'Original test captures with the model, capacity unit and variant visible.',
  },
  price: {
    label: 'Price anomaly', rule: 'Q1',
    summary: 'The captured prices are inconsistent with the reference range for this SSD variant.',
    evidence: ['The previous and current prices were checked against the same variant and currency.', 'The observed price warrants review alongside the other evidence.'],
    source: 'The captured listing and dated comparison refer to the same SSD variant.',
    agreement: 'The previous and current prices support the finding when checked against the reference range.',
    next: 'A dated, independent price comparison for the same variant and currency.',
  },
  reports: {
    label: 'Buyer reports', rule: 'Q4',
    summary: 'A buyer report raises a concern about the selected SSD option.',
    evidence: ['The report refers to the selected option.', 'A second independent report may help corroborate the issue.'],
    source: 'The report identifies the affected listing and option.',
    agreement: 'The report and listing point to the same option, with limited corroboration.',
    next: 'Another independent report with the exact option and supporting evidence.',
  },
  clear: {
    label: 'No flags found', rule: 'Q5',
    summary: 'The captured model, variant and reviewed buyer evidence agree with the reference.',
    evidence: ['The manufacturer catalog supports the listed capacity.', 'The reviewed reports show no qualifying discrepancy.'],
    source: 'The official catalog lists this model and capacity. Buyer evidence is indirect.',
    agreement: 'The listing and available buyer reports agree with the reference.',
    next: 'An original capacity test from a buyer of this exact variant.',
  },
} as const

export type ReviewSignal = keyof typeof signals
export const signalIds = ['unsupported', 'capacity', 'price', 'reports', 'clear'] as const

const confidenceFactors = [
  { label: 'Source quality', max: 35 },
  { label: 'Evidence agreement', max: 30 },
  { label: 'Evidence coverage', max: 20 },
  { label: 'Recency', max: 15 },
] as const

type Points = readonly [number, number, number, number]

export interface ReviewFinding {
  signal: ReviewSignal
  priority: ScoredPriority
  confidence: number
  points: Points
}

export interface ReviewCase {
  id: string
  sellerId: string
  listingId?: string
  shopId?: string
  sellerName: string
  title: string
  priority: ReviewPriority
  confidence: number | null
  findings: ReviewFinding[]
  demo: boolean
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

const fixture: ReadonlyArray<{
  priority: ReviewPriority
  signal?: ReviewSignal
  rows: ReadonlyArray<Points | null>
}> = [
  { priority: 'red', signal: 'capacity', rows: [[34, 29, 19, 14], [33, 27, 17, 14], [32, 26, 17, 13], [31, 26, 16, 12], [30, 24, 16, 12], [28, 24, 16, 12], [23, 20, 13, 9], [19, 17, 10, 8]] },
  { priority: 'red', signal: 'price', rows: [[31, 28, 17, 14], [25, 22, 15, 11]] },
  { priority: 'yellow', signal: 'reports', rows: [[24, 19, 14, 11], [17, 13, 10, 8]] },
  { priority: 'yellow', signal: 'capacity', rows: [[27, 22, 16, 12], [24, 20, 14, 10], [20, 16, 11, 9]] },
  { priority: 'yellow', signal: 'price', rows: [[29, 24, 16, 13], [26, 20, 16, 11], [24, 18, 13, 11], [15, 12, 9, 6]] },
  { priority: 'yellow', signal: 'reports', rows: [[26, 22, 16, 12], [18, 15, 11, 7]] },
  { priority: 'green', signal: 'clear', rows: [[33, 29, 18, 14], [32, 27, 18, 13], [31, 27, 17, 12], [30, 23, 17, 12], [26, 20, 15, 11], [23, 20, 14, 10], [23, 18, 13, 10]] },
  { priority: 'unknown', rows: [null, null, null] },
]

const models = ['Aster NV4', 'Harbor N700', 'Northstar X5', 'Cobalt V3', 'Lumen Pro']
const shops = ['Banyan Digital', 'Orbit Components', 'Byte Corner', 'Pine Circuit', 'Meridian IT', 'Copperlane Supply']

function finding(signal: ReviewSignal, priority: ScoredPriority, points: Points): ReviewFinding {
  return { signal, priority, points, confidence: points.reduce((total, value) => total + value, 0) }
}

const demoCases = fixture.flatMap(({ priority, signal, rows }) =>
  rows.map((points) => signal && points && priority !== 'unknown' ? [finding(signal, priority, points)] : []),
).map((findings, index) => {
  // Overlapping flags are distinct findings on the same SSD option.
  if (index === 0) findings.push(finding('price', 'yellow', [27, 21, 15, 12]))
  if (index === 10) findings.push(finding('unsupported', 'red', [31, 27, 16, 13]))
  findings.sort((a, b) => priorities[a.priority].rank - priorities[b.priority].rank || b.confidence - a.confidence)
  const id = 'SSD-' + (142 + index)
  return {
    id, sellerId: id,
    title: `${models[index % models.length]} ${[1, 2, 4][index % 3]} TB`,
    sellerName: shops[index % shops.length],
    priority: findings[0]?.priority ?? 'unknown',
    confidence: findings[0]?.confidence ?? null,
    findings,
    demo: true,
  } satisfies Omit<ReviewCase, 'status' | 'decision'>
})

function reviewStatus(decision?: Decision): InvestigationStatus {
  if (!decision) return 'To review'
  return decision.type === 'Need more information' ? 'In progress' : 'Resolved'
}

export function buildReviewCases(sellers: Seller[], decisions: Decision[]): ReviewCase[] {
  const demo = demoCases.map((item) => {
    const decision = decisions.find((result) => result.sellerId === item.id)
    return { ...item, decision, status: reviewStatus(decision) }
  })
  const submitted = sellers.filter((seller) => seller.id.startsWith('seller-new-')).flatMap((seller) =>
    seller.listings.map((listing, index): ReviewCase => {
      const decision = decisions.find((result) => result.sellerId === seller.id && result.listingId === listing.id)
        ?? decisions.find((result) => result.sellerId === seller.id && !result.listingId)
      // Older records stored template estimates. Only show prices from the new explicit capture.
      const captured = seller.submittedEvidence
      const complaint = seller.reports.find((report) => report.listingId === listing.id)?.complaint
      return {
        id: listing.id, sellerId: seller.id, listingId: listing.id, shopId: seller.shopId,
        title: captured ? listing.title : 'SSD listing ' + (index + 1),
        sellerName: seller.name, priority: 'unknown', confidence: null,
        findings: [], demo: false, decision, status: reviewStatus(decision),
        capture: {
          listingUrl: listing.listingUrl,
          referenceUrl: captured ? listing.referenceUrl : undefined,
          currentPrice: index === 0 ? captured?.currentPrice : undefined,
          previousPrice: captured ? listing.previousPrice : undefined,
          complaint: complaint === 'Buyer evidence was submitted with the captured listing sources.' ? undefined : complaint,
          photoCount: index === 0 ? captured?.photoCount : undefined,
        },
      }
    }),
  )
  return [...submitted, ...demo].sort((a, b) => priorities[a.priority].rank - priorities[b.priority].rank ||
    (b.confidence ?? -1) - (a.confidence ?? -1))
}

export function inConfidenceBand(score: number, band: ConfidenceBand) {
  const { min, max } = confidenceBands[band]
  return score >= min && score <= max
}

export function explainConfidence(result: ReviewFinding) {
  const [quality, agreement, coverage, recency] = result.points
  const signal = signals[result.signal]
  const reasons = [
    quality >= 30 ? signal.source : 'The available sources offer limited independent verification.',
    agreement >= 25 ? signal.agreement : 'The sources offer some support, with limited corroboration.',
    coverage >= 17 && result.signal === 'clear'
      ? 'Model, capacity and matching reviews are present. An original buyer test is missing.'
      : coverage >= 17 ? 'Core checks are covered, with some supporting evidence missing.'
      : 'At least one supporting source or check is incomplete.',
    recency >= 13 ? 'The listing capture is recent. A comparison source is slightly older.'
      : 'Older captures leave uncertainty about the current listing.',
  ]
  return confidenceFactors.map((factor, index) => ({ ...factor, points: result.points[index], reason: reasons[index] }))
}
