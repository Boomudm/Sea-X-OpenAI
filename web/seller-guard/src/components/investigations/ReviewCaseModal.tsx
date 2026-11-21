import { useEffect, useRef, useState, type FormEvent } from 'react'
import { X } from 'lucide-react'
import { explainConfidence, priorities, signals, type ReviewCase, type ReviewFinding, type ReviewSignal } from '../../data/reviewCases'
import { cn } from '../../lib/utils'
import type { Decision, DecisionType } from '../../types'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'

export interface ReviewSubmission {
  outcome: DecisionType
  notes: string
  flags?: Decision['flagDecisions']
  next: boolean
}

const evidenceTones = {
  red: 'border-[#efc9c1] bg-[#fdece8]/[.65]',
  yellow: 'border-[#eddbae] bg-[#fff3d8]/[.65]',
  green: 'border-[#c5e2d2] bg-[#e5f5ec]/[.65]',
}

export function ReviewCaseModal({ item, focusedSignal, onClose, onSave }: {
  item: ReviewCase
  focusedSignal?: ReviewSignal
  onClose: () => void
  onSave: (submission: ReviewSubmission) => void
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  const submitLock = useRef(false)
  const [notes, setNotes] = useState(item.decision?.notes ?? '')
  const [flagDecisions, setFlagDecisions] = useState<NonNullable<Decision['flagDecisions']>>(item.decision?.flagDecisions ?? {})
  const [outcome, setOutcome] = useState<'confirm' | 'request' | ''>(() => {
    if (item.priority === 'unknown' || item.decision?.type === 'Need more information') return 'request'
    if (item.decision?.type === 'No violation') return 'confirm'
    return ''
  })
  const [error, setError] = useState('')
  const flags = item.findings.filter(({ signal }) => signal !== 'clear')
  const activeFinding = item.findings.find(({ signal }) => signal === focusedSignal)
  const orderedFindings = activeFinding
    ? [activeFinding, ...item.findings.filter((finding) => finding !== activeFinding)]
    : item.findings

  useEffect(() => {
    const node = dialog.current
    if (!node) return
    node.showModal()
    heading.current?.focus({ preventScroll: true })
    return () => { if (node.open) node.close() }
  }, [])

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitLock.current) return
    if (!notes.trim()) {
      setError('Add a reviewer note before saving.')
      return
    }
    if (outcome !== 'request' && flags.some(({ signal }) => !flagDecisions[signal])) {
      setError('Accept or dismiss each flag, or request more evidence.')
      return
    }
    if (!flags.length && !outcome) {
      setError('Select a reviewer decision.')
      return
    }
    const result: DecisionType = outcome === 'request' ? 'Need more information'
      : flags.some(({ signal }) => flagDecisions[signal] === 'accepted') ? 'Violation confirmed'
      : 'No violation'
    const submitter = (event.nativeEvent as SubmitEvent).submitter
    submitLock.current = true
    onSave({ outcome: result, notes, flags: flags.length ? flagDecisions : undefined,
      next: submitter?.getAttribute('value') === 'next' })
  }

  return (
    <dialog
      ref={dialog}
      aria-labelledby="case-review-title"
      onCancel={(event) => { event.preventDefault(); onClose() }}
      className="review-modal m-auto w-[calc(100%-2rem)] max-w-3xl overflow-hidden rounded-2xl border border-line bg-white text-ink shadow-float"
    >
      <form className="review-modal-form flex flex-col" onSubmit={save}>
        <header className="flex shrink-0 items-start justify-between gap-3 border-b border-line p-4 sm:p-6">
          <div>
            <p className="text-sm font-semibold tracking-wide text-muted">Case {item.id}</p>
            <h2 ref={heading} tabIndex={-1} id="case-review-title" className="heading-5 mt-1 outline-none">{item.title}</h2>
            <p className="caption-5 mt-1 text-muted">{item.sellerName} · SSD listing</p>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Badge tone={priorities[item.priority].tone}>{priorities[item.priority].label}</Badge>
              <strong className="tabular-nums">{item.confidence === null ? 'Confidence unavailable'
                : `${item.confidence}% ${flags.length > 1 ? 'primary ' : ''}confidence`}</strong>
              {item.demo && <span className="caption-5 text-muted">Demo evidence</span>}
            </div>
          </div>
          <Button type="button" variant="outline" size="icon" aria-label="Close case" onClick={onClose}><X className="size-5" /></Button>
        </header>
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto overscroll-contain p-4 sm:p-6">
          {orderedFindings.length ? orderedFindings.map((finding, index) => (
            <FindingPanel key={finding.signal} finding={finding} primary={index === 0}>
              {finding.signal !== 'clear' && (
                <fieldset className="mt-4">
                  <legend className="font-semibold">Reviewer decision for {signals[finding.signal].label.toLowerCase()}</legend>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(['accepted', 'dismissed'] as const).map((choice) => (
                      <label key={choice} className="flex cursor-pointer items-center gap-2 rounded-lg border border-line px-3 py-2 has-[:checked]:border-brand/40 has-[:checked]:bg-peach">
                        <input
                          className="accent-brand"
                          type="radio"
                          name={`flag-${finding.signal}`}
                          checked={flagDecisions[finding.signal] === choice}
                          onChange={() => {
                            setFlagDecisions((previous) => ({ ...previous, [finding.signal]: choice }))
                            setError('')
                          }}
                        />
                        {choice === 'accepted' ? 'Accept flag' : 'Dismiss flag'}
                      </label>
                    ))}
                  </div>
                </fieldset>
              )}
            </FindingPanel>
          )) : <CapturedEvidence item={item} />}

          {item.priority === 'unknown' ? (
            <p className="rounded-lg border border-line bg-canvas p-3 text-sm">Saving this case records a request for more evidence.</p>
          ) : flags.length ? (
            <label className="flex items-center gap-2 text-sm font-medium">
              <input type="checkbox" className="accent-brand" checked={outcome === 'request'}
                onChange={(event) => { setOutcome(event.target.checked ? 'request' : ''); setError('') }} />
              Request more evidence before resolving
            </label>
          ) : (
            <fieldset>
              <legend className="font-semibold">Reviewer decision</legend>
              <div className="mt-2 flex flex-wrap gap-2">
                {(['confirm', 'request'] as const).map((choice) => (
                  <label key={choice} className="flex cursor-pointer items-center gap-2 rounded-lg border border-line px-3 py-2 has-[:checked]:border-brand/40 has-[:checked]:bg-peach">
                    <input type="radio" name="case-outcome" className="accent-brand" checked={outcome === choice}
                      onChange={() => { setOutcome(choice); setError('') }} />
                    {choice === 'confirm' ? 'Confirm review' : 'Request evidence'}
                  </label>
                ))}
              </div>
            </fieldset>
          )}
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

function FindingPanel({ finding, primary, children }: { finding: ReviewFinding; primary: boolean; children?: React.ReactNode }) {
  const signal = signals[finding.signal]
  const earlyCapacity = finding.signal === 'capacity' && finding.priority === 'yellow'
  const lowPrice = finding.signal === 'price' && finding.priority === 'yellow'
  const rule = earlyCapacity || lowPrice ? 'Q4' : signal.rule
  const evidence = earlyCapacity
    ? ['The listing identifies the advertised capacity.', 'One buyer test is available for this variant.']
    : signal.evidence

  return (
    <section className="rounded-xl border border-line p-4">
      <div className={cn('rounded-lg border p-3', evidenceTones[finding.priority])}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-lg font-semibold">{earlyCapacity ? 'Reported capacity shortfall' : signal.label}</h3>
          <div className="flex items-center gap-2">
            <Badge tone={priorities[finding.priority].tone}>{priorities[finding.priority].label}</Badge>
            <span className="text-sm font-semibold tabular-nums">{finding.confidence}%</span>
          </div>
        </div>
        <p className="body-3 mt-2">{earlyCapacity ? 'One buyer reported a smaller usable capacity. A second test is needed.' : signal.summary}</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">
          {evidence.map((entry) => <li key={entry}>{entry}</li>)}
        </ul>
      </div>
      <details open={primary} className="mt-3 rounded-lg bg-canvas p-3">
        <summary className="focus-ring cursor-pointer rounded font-semibold">Why {finding.confidence}% confidence?</summary>
        <p className="caption-5 mt-2 text-muted">Evidence factors for {rule} · Demo scoring</p>
        <dl className="mt-3 grid gap-2 min-[480px]:grid-cols-2">
          {explainConfidence(finding).map(({ label, max, points, reason }) => (
            <div key={label} className="rounded-md border border-line bg-white p-3">
              <dt className="flex justify-between gap-2 text-sm font-semibold">{label}<span className="shrink-0 tabular-nums">{points} / {max}</span></dt>
              <dd className="caption-5 mt-1 text-muted">{reason}</dd>
            </div>
          ))}
        </dl>
        <p className="caption-5 mt-3 text-muted"><strong>What would help:</strong> {signal.next}</p>
      </details>
      {children}
    </section>
  )
}

function CapturedEvidence({ item }: { item: ReviewCase }) {
  const capture = item.capture
  const sourceLinks = [
    { label: 'Open listing', url: safeHttpUrl(capture?.listingUrl) },
    { label: 'Open official reference', url: safeHttpUrl(capture?.referenceUrl) },
  ].filter(({ url }) => url)
  return (
    <section className="rounded-lg border border-line bg-canvas p-4">
      <h3 className="text-lg font-semibold">Confidence unavailable</h3>
      <p className="body-3 mt-2 text-muted">Confirm the exact SSD variant and add a matching reference or buyer test to assess this case.</p>
      {sourceLinks.length > 0 && <div className="mt-3 flex flex-wrap gap-3">{sourceLinks.map(({ label, url }) => (
        <a key={label} className="focus-ring rounded font-semibold text-[#a82d18] hover:underline" href={url} target="_blank" rel="noreferrer">{label}</a>
      ))}</div>}
      {capture?.previousPrice !== undefined && <p className="caption-5 mt-2">Entered previous price: {capture.previousPrice.toLocaleString()}</p>}
      {capture?.currentPrice !== undefined && <p className="caption-5 mt-2">Entered current price: {capture.currentPrice.toLocaleString()}</p>}
      {capture?.complaint && <p className="body-3 mt-2"><strong>Submitted buyer report:</strong> {capture.complaint}</p>}
      {Boolean(capture?.photoCount) && <p className="caption-5 mt-2 text-muted">Photo count recorded: {capture?.photoCount}. Image files are unavailable in the demo.</p>}
    </section>
  )
}

function safeHttpUrl(value?: string) {
  if (!value) return undefined
  try {
    const url = new URL(value)
    if ((url.protocol === 'http:' || url.protocol === 'https:') && !url.username && !url.password) return url.href
  } catch {
    return undefined
  }
  return undefined
}
