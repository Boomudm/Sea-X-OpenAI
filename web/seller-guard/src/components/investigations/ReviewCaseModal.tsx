import { useEffect, useRef, useState, type FormEvent } from 'react'
import { X } from 'lucide-react'
import { publicText, type EvidenceSource, type PipelineCase, type PipelineEvidence } from '../../data/pipelineCases'
import { caseVerdict, priorities, type ReviewCase } from '../../data/reviewCases'
import { keyedItems } from '../../lib/utils'
import type { DecisionType } from '../../types'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'

export interface ReviewSubmission {
  outcome: DecisionType
  notes: string
  next: boolean
}

const OUTCOMES: DecisionType[] = ['Shortfall confirmed', 'Not confirmed', 'Need more information']
const CHECKS: Record<string, string> = {
  Q1: 'Price check', Q2: 'Brand capacity check', Q3: 'Measured buyer shortfalls',
  Q4: 'Manual checks', Q5: 'Matched reviews', grey: 'Evidence coverage',
}
const PATH_STATES: Record<string, string> = {
  decided: 'Set priority', triggered: 'Also triggered', clear: 'No reason recorded',
}

export function ReviewCaseModal({ item, onClose, onSave }: Readonly<{
  item: ReviewCase
  onClose: () => void
  onSave: (submission: ReviewSubmission) => void
}>) {
  const dialog = useRef<HTMLDialogElement>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  const submitLock = useRef(false)
  const [notes, setNotes] = useState(item.decision?.notes ?? '')
  const [outcome, setOutcome] = useState<DecisionType | ''>(item.decision?.type ?? '')
  const [error, setError] = useState('')
  const subtitle = [item.sellerName, item.variant].filter(Boolean).join(' · ')

  useEffect(() => {
    const node = dialog.current
    if (!node) return
    node.showModal()
    heading.current?.focus({ preventScroll: true })
    return () => { if (node.open) node.close() }
  }, [])

  function close() {
    const dirty = notes !== (item.decision?.notes ?? '') || outcome !== (item.decision?.type ?? '')
    if (!dirty || window.confirm('Discard the unsaved reviewer decision?')) onClose()
  }

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitLock.current) return
    if (!outcome || !notes.trim()) {
      setError('Choose a decision and add a reviewer note before saving.')
      return
    }
    const submitter = (event.nativeEvent as SubmitEvent).submitter
    submitLock.current = true
    onSave({ outcome, notes, next: submitter?.getAttribute('value') === 'next' })
  }

  return (
    <dialog
      ref={dialog}
      aria-labelledby="case-review-title"
      onCancel={(event) => { event.preventDefault(); close() }}
      className="review-modal fixed inset-0 m-0 h-full !max-h-none w-full max-w-none overflow-hidden border-0 bg-transparent p-0 open:grid open:place-items-center"
    >
      <button type="button" aria-label="Close case from backdrop" tabIndex={-1}
        className="absolute inset-0 cursor-default bg-transparent"
        onMouseDown={(event) => event.preventDefault()} onClick={close} />
      <form className="review-modal-form relative flex w-[calc(100%-2rem)] max-w-3xl flex-col overflow-hidden rounded-2xl border border-line bg-white text-ink shadow-float" onSubmit={save}>
        <header className="flex shrink-0 items-start justify-between gap-3 border-b border-line p-4 sm:p-6">
          <div>
            <p className="text-sm font-semibold tracking-wide text-muted">Case {item.caseLabel}</p>
            <h2 ref={heading} tabIndex={-1} id="case-review-title" className="heading-5 mt-1 outline-none">{item.title}</h2>
            {subtitle && <p className="caption-5 mt-1 text-muted">{subtitle}</p>}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Badge tone={priorities[item.priority].tone}>{priorities[item.priority].label}</Badge>
              <strong className="tabular-nums">{item.confidence === null ? 'Confidence unavailable' : `${item.confidence}% confidence`}</strong>
              {item.source === 'sample' && <Badge>Sample data</Badge>}
            </div>
            <p className="caption-5 mt-2 text-muted">Verdict · {caseVerdict(item.decision)}</p>
          </div>
          <Button type="button" variant="outline" size="icon" aria-label="Close case" onClick={close}><X className="size-5" /></Button>
        </header>
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain p-4 sm:p-6">
          {item.pipeline ? <PipelineDetails item={item} report={item.pipeline} /> : <CaptureDetails item={item} />}
          <fieldset>
            <legend className="font-semibold">Reviewer decision</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {OUTCOMES.map((choice) => (
                <label key={choice} className="flex min-h-11 cursor-pointer items-center gap-2 rounded-lg border border-line px-3 py-2 has-[:checked]:border-brand/40 has-[:checked]:bg-peach">
                  <input type="radio" name="case-outcome" className="accent-brand" checked={outcome === choice}
                    onChange={() => { setOutcome(choice); setError('') }} />
                  {choice}
                </label>
              ))}
            </div>
          </fieldset>
          <label className="block font-semibold">
            Reviewer note
            <textarea
              value={notes} onChange={(event) => { setNotes(event.target.value); setError('') }}
              maxLength={500} className="form-control mt-2 block min-h-24 w-full resize-y py-3 font-normal"
              placeholder="Record the evidence behind your decision."
            />
          </label>
          {error && <p role="alert" className="text-sm font-semibold text-red-700">{error}</p>}
        </div>
        <footer className="flex shrink-0 flex-wrap justify-end gap-2 border-t border-line bg-white p-4 sm:p-6">
          <Button type="submit" value="save" variant="outline">Save decision</Button>
          <Button type="submit" value="next">Save &amp; next</Button>
        </footer>
      </form>
    </dialog>
  )
}

function PipelineDetails({ item, report }: Readonly<{ item: ReviewCase; report: PipelineCase }>) {
  const [primary, ...other] = report.reasons
  const hasMarketRange = report.evidence.some((entry) => entry.source === 'market_range')
  return (
    <>
      <section className="space-y-3 rounded-lg border border-line bg-canvas p-4" aria-label="Pipeline evidence">
        <h3 className="text-lg font-semibold">{primary ? publicText(primary) : 'Review evidence'}</h3>
        {other.length > 0 && <ul className="list-disc space-y-1 pl-5 text-sm">
          {other.map((reason) => <li key={reason}>{publicText(reason)}</li>)}
        </ul>}
        <CaptureDetails item={item} showPrices={!hasMarketRange} />
        {report.evidence.map((entry) => <EvidenceEntry key={JSON.stringify(entry)} entry={entry} />)}
      </section>
      <details open className="rounded-lg border border-line bg-white p-4">
        <summary className="focus-ring cursor-pointer rounded font-semibold">Why {report.confidence}% confidence?</summary>
        <p className="mt-2 text-sm text-muted">The rules start at 50 points. These adjustments were recorded for this option.</p>
        {report.adjustments.length > 0 && <ul className="mt-2 space-y-2 text-sm">
          {keyedItems(report.adjustments).map(({ item: { points, reason }, key }) =>
            <li key={key}><strong className="tabular-nums">{points > 0 ? '+' : ''}{points}</strong> · {publicText(reason)}</li>)}
        </ul>}
        <p className="mt-2 text-sm text-muted">Base after standard checks · {report.base}%</p>
        {report.missing_evidence.length > 0 && <>
          <h3 className="mt-3 font-semibold">Evidence still needed</h3>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">
            {keyedItems(report.missing_evidence).map(({ item: missing, key }) => <li key={key}>{publicText(missing)}</li>)}
          </ul>
        </>}
      </details>
      {report.path.length > 0 && <details className="rounded-lg border border-line bg-white p-4">
        <summary className="focus-ring cursor-pointer rounded font-semibold">Decision path</summary>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
          {report.path.map((entry) => {
            const [check, state] = entry.split(': ')
            return <li key={entry}>{CHECKS[check] && PATH_STATES[state]
              ? `${CHECKS[check]} · ${PATH_STATES[state]}`
              : publicText(entry)}</li>
          })}
        </ol>
      </details>}
    </>
  )
}

const thb = new Intl.NumberFormat('en', { style: 'currency', currency: 'THB', maximumFractionDigits: 2, minimumFractionDigits: 0 })
const percent = new Intl.NumberFormat('en', { style: 'percent', maximumFractionDigits: 1 })

function Money({ label, amount }: Readonly<{ label: string; amount?: number | null }>) {
  return typeof amount === 'number' && Number.isFinite(amount)
    ? <p>{label} <strong className="tabular-nums">{thb.format(amount)}</strong></p> : null
}

type EvidenceProps = Readonly<{ entry: PipelineEvidence }>

function EvidenceEntry({ entry }: EvidenceProps) {
  switch (entry.source) {
    case 'review':
      return <BuyerReviewEvidence entry={entry} />
    case 'market_range':
      return <MarketRangeEvidence entry={entry} />
    case 'brand_page':
    case 'mall_capacities':
      return <CapacityEvidence entry={entry} />
    case 'review_count':
      if (typeof entry.matched_text_reviews !== 'number' || typeof entry.checked_text_reviews !== 'number') return null
      return <p className="text-sm text-muted">{entry.checked_text_reviews} of {entry.matched_text_reviews} matched text reviews checked</p>
    case 'option':
      return entry.capacity_text
        ? <p className="text-sm">Captured capacity · {publicText(entry.capacity_text)}</p> : null
    default:
      return null
  }
}

function BuyerReviewEvidence({ entry }: EvidenceProps) {
  const buyer = typeof entry.buyer_masked === 'string' && /[*…•]/.test(entry.buyer_masked)
    ? publicText(entry.buyer_masked) : 'Buyer'
  const quantity = typeof entry.quantity === 'number' && entry.unit && entry.unit !== 'none'
    ? `${entry.quantity} ${publicText(entry.unit)}` : undefined
  const ratio = typeof entry.ratio === 'number' && Number.isFinite(entry.ratio)
    ? percent.format(entry.ratio) + ' of advertised capacity' : undefined
  return <blockquote className="rounded-r-lg border-l-2 border-line bg-white px-3 py-2 text-sm">
    {entry.quote && <p className="whitespace-pre-wrap">{publicText(entry.quote)}</p>}
    <footer className="mt-1 text-muted">{[buyer, entry.date, quantity, ratio].filter(Boolean).join(' · ')}</footer>
  </blockquote>
}

function MarketRangeEvidence({ entry }: EvidenceProps) {
  return (
    <div className="space-y-2 rounded-lg bg-white p-3 text-sm">
      <h4 className="font-semibold">Market comparison</h4>
      <div className="flex flex-wrap gap-x-5 gap-y-1">
        <Money label="Was" amount={entry.was_thb} /><Money label="Now" amount={entry.now_thb} />
        {typeof entry.low_thb === 'number' && typeof entry.high_thb === 'number' &&
          <p>Range <strong>{thb.format(entry.low_thb)}–{thb.format(entry.high_thb)}</strong></p>}
      </div>
      {entry.date && <p className="text-muted">Captured {entry.date}</p>}
      {keyedItems(entry.sources ?? []).map(({ item: offer, key }) => <SourceOffer key={key} offer={offer} />)}
    </div>
  )
}

function CapacityEvidence({ entry }: EvidenceProps) {
  return (
    <div className="space-y-2 rounded-lg bg-white p-3 text-sm">
      <h4 className="font-semibold">{entry.source === 'brand_page' ? 'Brand capacity list' : 'Official Mall capacity list'}</h4>
      {entry.capacities_gb && entry.capacities_gb.length > 0 && <p>{entry.capacities_gb.map((capacity) => `${capacity} GB`).join(', ')}</p>}
      {typeof entry.promise_gb === 'number' && <p>Advertised option · {entry.promise_gb} GB</p>}
      {entry.date && <p className="text-muted">Captured {entry.date}</p>}
      <SourceLink label="Brand reference" value={entry.url} />
      {keyedItems(entry.sources ?? []).map(({ item: offer, key }) => <SourceOffer key={key} offer={offer} />)}
    </div>
  )
}

function SourceOffer({ offer }: Readonly<{ offer: EvidenceSource }>) {
  return <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
    <SourceLink label="Official offer" value={offer.url} />
    <Money label="Now" amount={offer.now_thb} />
    {offer.date && <span className="text-muted">{offer.date}</span>}
  </div>
}

function CaptureDetails({ item, showPrices = true }: Readonly<{ item: ReviewCase; showPrices?: boolean }>) {
  const capture = item.capture
  if (!capture) return null
  return (
    <div className="space-y-2 text-sm">
      {!item.pipeline && <p>Collect evidence for this listing before assigning a review priority.</p>}
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        <SourceLink label="Listing source" value={capture.listingUrl} />
        <SourceLink label="Official reference" value={capture.referenceUrl} />
      </div>
      {showPrices && <div className="flex flex-wrap gap-x-4 gap-y-1">
        <Money label="Was" amount={capture.previousPrice} /><Money label="Now" amount={capture.currentPrice} />
      </div>}
      {capture.complaint && <p><strong>Submitted buyer report:</strong> {publicText(capture.complaint)}</p>}
      {typeof capture.photoCount === 'number' && <p className="text-muted">Photos recorded · {capture.photoCount}</p>}
    </div>
  )
}

function SourceLink({ label, value }: Readonly<{ label: string; value?: string }>) {
  if (!value) return null
  try {
    const url = new URL(value)
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return null
    if (url.hostname.endsWith('.invalid')) return <span className="text-muted">{label} · {url.hostname}{url.pathname}</span>
    return <a className="focus-ring rounded font-semibold text-[#a82d18] hover:underline" href={url.href}
      target="_blank" rel="noreferrer">{label}</a>
  } catch {
    return null
  }
}
