export type PipelineSignal = 'capacity' | 'unsupported' | 'price' | 'reports' | 'clear'
export type PipelinePriority = 'red' | 'yellow' | 'green' | 'unknown'

export interface EvidenceSource {
  url?: string
  date?: string
  now_thb?: number
}

export interface PipelineEvidence extends EvidenceSource {
  source: string
  quote?: string
  ratio?: number | null
  buyer_masked?: string
  quantity?: number | null
  unit?: string
  capacities_gb?: number[]
  promise_gb?: number
  was_thb?: number | null
  low_thb?: number
  high_thb?: number
  checked_text_reviews?: number
  matched_text_reviews?: number
  capacity_text?: string
  sources?: EvidenceSource[]
}

export interface PipelineCase {
  listing_id: string
  option_id: string
  title: string | null
  variation_label: string | null
  priority: PipelinePriority
  confidence: number
  base: number
  adjustments: { points: number; reason: string }[]
  deciding: string
  findings: PipelineSignal[]
  path: string[]
  reasons: string[]
  evidence: PipelineEvidence[]
  missing_evidence: string[]
  capture: {
    listing_url?: string
    was_thb?: number | null
    now_thb?: number
    photo_count?: number
    listing_images?: string[]
    buyer_images?: string[]
  }
}

export type CaptureFeed =
  | { state: 'loading' | 'missing' | 'error' }
  | { state: 'available'; cases: PipelineCase[] }

const priorities = new Set(['red', 'yellow', 'green', 'unknown'])
const signals = new Set(['capacity', 'unsupported', 'price', 'reports', 'clear'])

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function strings(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((entry) => typeof entry === 'string')
}

function score(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0 && value <= 100
}

function isPipelineCase(value: unknown): value is PipelineCase {
  return record(value) &&
    typeof value.listing_id === 'string' && value.listing_id.length > 0 &&
    typeof value.option_id === 'string' && value.option_id.length > 0 &&
    (value.title === null || typeof value.title === 'string') &&
    (value.variation_label === null || typeof value.variation_label === 'string') &&
    typeof value.priority === 'string' && priorities.has(value.priority) &&
    score(value.confidence) && score(value.base) && typeof value.deciding === 'string' &&
    strings(value.findings) && value.findings.every((finding) => signals.has(finding)) &&
    strings(value.path) && strings(value.reasons) && strings(value.missing_evidence) &&
    Array.isArray(value.adjustments) && value.adjustments.every((adjustment: unknown) =>
      record(adjustment) && typeof adjustment.points === 'number' &&
      Number.isFinite(adjustment.points) && typeof adjustment.reason === 'string') &&
    Array.isArray(value.evidence) && value.evidence.every((entry: unknown) =>
      record(entry) && typeof entry.source === 'string') &&
    record(value.capture) &&
    (value.capture.listing_images === undefined || strings(value.capture.listing_images)) &&
    (value.capture.buyer_images === undefined || strings(value.capture.buyer_images))
}

export async function loadCapturedCases(signal: AbortSignal): Promise<CaptureFeed> {
  const response = await fetch('/data/cases.json', { signal, cache: 'no-store' })
  // Static SPA hosts may serve the app's HTML shell for a missing JSON file.
  if (response.status === 404) return { state: 'missing' }
  if (!response.ok) return { state: 'error' }
  if (response.headers.get('content-type')?.includes('text/html')) {
    return { state: 'missing' }
  }
  const data: unknown = await response.json()
  if (!Array.isArray(data) || !data.every(isPipelineCase)) return { state: 'error' }
  return { state: 'available', cases: data }
}

export function publicText(text: string) {
  return text.replace(/\b(?:fake|fraud)\b/gi, '[redacted]')
}
