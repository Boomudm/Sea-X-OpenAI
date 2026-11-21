import { useMemo, useState } from 'react'
import { ArrowLeft, BrainCircuit, Check, CheckCircle2, ChevronRight, CircleAlert, ExternalLink, FileCheck2, Image, Link2, Scale, X } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Dialog } from '../components/ui/Dialog'
import { useToast } from '../components/ui/Toast'
import { useInvestigations } from '../hooks/useInvestigations'
import { cn, formatCurrency, treeResult, type TreeResult } from '../lib/utils'
import type { DecisionType } from '../types'

type WorkspaceStep = 'capture' | 'findings' | 'decision'
type FlagState = 'accepted' | 'dismissed'

const flagDefinitions = [
  { id: 'capacity', label: 'Capacity or specification mismatch', detail: 'Advertised attributes do not align with the buyer evidence.' },
  { id: 'price', label: 'Market price anomaly', detail: 'The current price sits below the reference market range.' },
  { id: 'twoPrice', label: 'Two price inconsistency', detail: 'Previous and current prices create an unusual promotion gap.' },
  { id: 'reports', label: 'Repeated buyer report pattern', detail: 'Similar complaints occur across multiple listings.' },
  { id: 'photos', label: 'Buyer photo mismatch', detail: 'The received item differs from the advertised image.' },
] as const

const resultTone: Record<TreeResult, 'red' | 'yellow' | 'green' | 'neutral'> = { Red: 'red', Yellow: 'yellow', Green: 'green', Grey: 'neutral' }

export function InvestigationWorkspacePage() {
  const { sellerId = '' } = useParams()
  const { getSeller, submitDecision } = useInvestigations()
  const seller = getSeller(sellerId)
  const navigate = useNavigate()
  const { toast } = useToast()
  const [step, setStep] = useState<WorkspaceStep>('capture')
  const [listingIndex, setListingIndex] = useState(0)
  const [flags, setFlags] = useState<Record<string, FlagState>>({})
  const [notes, setNotes] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [noteError, setNoteError] = useState('')

  const listing = seller?.listings[listingIndex]
  const tree = seller ? treeResult(seller.riskScore) : 'Grey'
  const checks = useMemo(() => seller && listing ? [
    { label: 'Capacity check', passed: listing.findings.some((finding) => finding.result === 'Mismatch'), result: 'Mismatch detected' },
    { label: 'Market price check', passed: Boolean(listing.marketPriceMin && listing.price < listing.marketPriceMin), result: `${formatCurrency(listing.price)} vs ${formatCurrency(listing.marketPriceMin ?? listing.price)} minimum` },
    { label: 'Two price check', passed: Boolean(listing.previousPrice && listing.previousPrice > listing.price * 1.3), result: `${formatCurrency(listing.previousPrice ?? listing.price)} before, ${formatCurrency(listing.price)} now` },
    { label: 'Review pattern', passed: seller.reports.length >= 3, result: `${seller.reports.length} related buyer reports` },
    { label: 'Photo comparison', passed: listing.findings.some((finding) => finding.result === 'Mismatch'), result: 'Visual model mismatch found' },
  ] : [], [seller, listing])

  if (!seller || !listing) {
    return <div className="page-container"><div className="surface p-8"><h1 className="heading-5">Case not found</h1><p className="body-6 mt-2 text-muted">This investigation is not available in the review queue.</p><Button className="mt-6" onClick={() => navigate('/')}>Return to review queue</Button></div></div>
  }

  const resolvedFlags = Object.keys(flags).length
  const acceptedFlags = Object.values(flags).filter((value) => value === 'accepted').length
  const decisionType: DecisionType = resolvedFlags < flagDefinitions.length ? 'Need more information' : acceptedFlags > 0 ? 'Violation confirmed' : 'No violation'

  const prepareDecision = () => {
    if (resolvedFlags < flagDefinitions.length) {
      setNoteError('Accept or dismiss every flag before saving the decision.')
      return
    }
    if (notes.trim().length < 20) {
      setNoteError('Add a reviewer note of at least 20 characters.')
      return
    }
    setNoteError('')
    setConfirmOpen(true)
  }

  const saveDecision = () => {
    submitDecision(seller.id, decisionType, notes, flags)
    setConfirmOpen(false)
    toast(`Decision saved for ${seller.name}.`)
    navigate('/')
  }

  return (
    <div className="page-container">
      <Link to="/" className="focus-ring inline-flex items-center gap-2 rounded-lg text-base font-semibold text-muted hover:text-ink"><ArrowLeft className="size-4" />Back to review queue</Link>

      <section className="organic-panel mt-4 rounded-xl border border-line bg-white p-6 shadow-soft md:p-8" aria-labelledby="case-title">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-start">
          <div className="flex min-w-0 flex-col gap-5 sm:flex-row">
            <img src={listing.advertisedImage} alt={listing.title} className="size-28 shrink-0 rounded-xl object-cover" />
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2"><Badge tone={resultTone[tree]}>Tree result: {tree}</Badge><Badge tone="orange">Ready for review</Badge></div>
              <h1 id="case-title" className="heading-3 mt-3">{seller.name}</h1>
              <p className="body-6 mt-2 text-muted">Shop ID {seller.shopId} · {seller.listings.length} captured listings · {seller.reports.length} buyer reports</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:min-w-72">
            <Metric label="Tree score" value={`${seller.riskScore}/100`} tone="text-brand" />
            <Metric label="Confidence" value={`${seller.confidence}%`} />
          </div>
        </div>
        <p className="body-3 mt-6 max-w-4xl text-muted">{seller.summary}</p>
      </section>

      <nav className="mt-4 grid gap-2 rounded-xl border border-line bg-white p-2 shadow-soft sm:grid-cols-3" aria-label="Investigation steps">
        {([
          ['capture', '01', 'Captured data'],
          ['findings', '02', 'Automated findings'],
          ['decision', '03', 'Human decision'],
        ] as const).map(([id, number, label]) => (
          <button key={id} onClick={() => setStep(id)} className={cn('focus-ring flex items-center gap-3 rounded-lg px-4 py-3 text-left text-base font-semibold transition-colors duration-300 hover:bg-canvas', step === id ? 'bg-peach text-brand' : 'text-muted')}>
            <span className={cn('flex size-8 items-center justify-center rounded-lg text-sm font-semibold', step === id ? 'bg-brand text-white' : 'bg-stone-100 text-ink')}>{number}</span>{label}<ChevronRight className="ml-auto size-4" />
          </button>
        ))}
      </nav>

      {step === 'capture' && <CapturedData seller={seller} listing={listing} listingIndex={listingIndex} setListingIndex={setListingIndex} onNext={() => setStep('findings')} />}
      {step === 'findings' && <AutomatedFindings seller={seller} listing={listing} tree={tree} checks={checks} onNext={() => setStep('decision')} />}
      {step === 'decision' && (
        <section className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
          <div className="surface p-6">
            <div className="flex items-start gap-3"><span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-peach text-brand"><FileCheck2 className="size-5" /></span><div><h2 className="heading-5">Review each flag</h2><p className="body-6 mt-1 text-muted">Accept or dismiss every system flag. Your decision does not change the deterministic tree result.</p></div></div>
            <div className="mt-6 space-y-3">
              {flagDefinitions.map((flag) => (
                <article key={flag.id} className="rounded-xl border border-line p-4">
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
                    <div className="flex-1"><h3 className="text-base font-semibold text-ink">{flag.label}</h3><p className="body-6 mt-1 text-muted">{flag.detail}</p></div>
                    <div className="grid grid-cols-2 gap-2">
                      <button onClick={() => setFlags((current) => ({ ...current, [flag.id]: 'accepted' }))} className={cn('focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-lg border px-3 text-base font-semibold transition-colors duration-300', flags[flag.id] === 'accepted' ? 'border-emerald-600 bg-emerald-50 text-emerald-800' : 'border-line bg-white text-muted hover:bg-canvas')}><Check className="size-4" />Accept</button>
                      <button onClick={() => setFlags((current) => ({ ...current, [flag.id]: 'dismissed' }))} className={cn('focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-lg border px-3 text-base font-semibold transition-colors duration-300', flags[flag.id] === 'dismissed' ? 'border-stone-500 bg-stone-100 text-ink' : 'border-line bg-white text-muted hover:bg-canvas')}><X className="size-4" />Dismiss</button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
            <label className="mt-6 block"><span className="text-base font-semibold text-ink">Reviewer notes</span><textarea value={notes} onChange={(event) => setNotes(event.target.value)} className="form-control mt-2 min-h-32 w-full resize-y py-3" placeholder="Explain which evidence supports the final decision." /></label>
            {noteError && <p className="mt-2 text-sm font-medium text-red-700" role="alert">{noteError}</p>}
          </div>
          <aside className="surface h-fit p-6 xl:sticky xl:top-20">
            <p className="eyebrow">Decision summary</p><h2 className="heading-6 mt-2">{decisionType}</h2>
            <dl className="mt-5 space-y-3 text-base"><SummaryRow label="Tree result" value={tree} /><SummaryRow label="Confidence" value={`${seller.confidence}%`} /><SummaryRow label="Flags reviewed" value={`${resolvedFlags}/${flagDefinitions.length}`} /><SummaryRow label="Flags accepted" value={String(acceptedFlags)} /></dl>
            <div className="mt-6 rounded-lg bg-canvas p-4"><p className="text-sm font-semibold text-ink">System boundary</p><p className="caption-5 mt-1 text-muted">The decision tree sets the color. AI explains evidence and confidence but cannot override it.</p></div>
            <Button className="mt-6 w-full" onClick={prepareDecision}>Save human decision</Button>
          </aside>
        </section>
      )}

      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)} title="Save this decision?" description={`This will mark ${seller.name} as ${decisionType.toLowerCase()} and return the case to the queue.`}>
        <div className="flex justify-end gap-3"><Button variant="ghost" onClick={() => setConfirmOpen(false)}>Keep reviewing</Button><Button onClick={saveDecision}>Confirm decision</Button></div>
      </Dialog>
    </div>
  )
}

function CapturedData({ seller, listing, listingIndex, setListingIndex, onNext }: { seller: ReturnType<typeof useInvestigations>['sellers'][number]; listing: ReturnType<typeof useInvestigations>['sellers'][number]['listings'][number]; listingIndex: number; setListingIndex: (value: number) => void; onNext: () => void }) {
  return (
    <section className="mt-4 grid gap-4 xl:grid-cols-[280px_minmax(0,1fr)]">
      <aside className="surface h-fit p-4"><h2 className="text-base font-semibold text-ink">Captured listings</h2><div className="mt-3 space-y-2">{seller.listings.map((item, index) => <button key={item.id} onClick={() => setListingIndex(index)} className={cn('focus-ring flex w-full items-center gap-3 rounded-lg p-3 text-left transition-colors duration-300', index === listingIndex ? 'bg-peach text-brand' : 'hover:bg-canvas')}><img src={item.advertisedImage} alt="" className="size-10 rounded-lg object-cover" /><span className="min-w-0"><strong className="block truncate text-sm font-semibold">{item.title}</strong><span className="block text-sm text-muted">{item.sku}</span></span></button>)}</div></aside>
      <div className="space-y-4">
        <article className="surface p-6"><div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between"><div><p className="eyebrow">Listing source</p><h2 className="heading-5 mt-2">{listing.title}</h2><p className="body-6 mt-1 text-muted">{listing.category} · {listing.sku}</p></div>{listing.listingUrl && <a href={listing.listingUrl} target="_blank" rel="noreferrer" className="focus-ring inline-flex items-center gap-2 rounded-lg text-base font-semibold text-brand hover:underline">Open listing <ExternalLink className="size-4" /></a>}</div>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><Metric label="Previous price" value={formatCurrency(listing.previousPrice ?? listing.price)} /><Metric label="Current price" value={formatCurrency(listing.price)} tone="text-brand" /><Metric label="Market minimum" value={formatCurrency(listing.marketPriceMin ?? listing.price)} /><Metric label="Market maximum" value={formatCurrency(listing.marketPriceMax ?? listing.price)} /></div>
          {listing.referenceUrl && <a href={listing.referenceUrl} target="_blank" rel="noreferrer" className="focus-ring mt-5 inline-flex items-center gap-2 rounded text-base font-medium text-muted hover:text-brand"><Link2 className="size-4" />Official Mall or brand reference<ExternalLink className="size-4" /></a>}
        </article>
        <article className="surface p-6"><div className="flex items-center gap-3"><Image className="size-5 text-brand" /><h2 className="heading-6">Listing photo vs buyer evidence</h2></div><div className="mt-5 grid gap-4 md:grid-cols-2"><Photo label="Advertised listing" src={listing.advertisedImage} alt={`Advertised ${listing.title}`} /><Photo label="Received by buyer" src={listing.receivedImage} alt={`Buyer received item for ${listing.title}`} /></div><div className="mt-4 rounded-lg bg-peach p-4"><p className="text-base font-semibold text-ink">Observed difference</p><p className="body-6 mt-1 text-muted">{listing.discrepancy}</p></div></article>
        <article className="surface p-6"><h2 className="heading-6">Buyer reports and reviews</h2><div className="mt-4 space-y-3">{seller.reports.map((report) => <div key={report.id} className="rounded-lg bg-canvas p-4"><p className="body-3 text-ink">“{report.complaint}”</p><p className="caption-5 mt-2 text-muted">{report.attachedImages} images · {report.evidenceStatus}</p></div>)}</div></article>
        <div className="flex justify-end"><Button onClick={onNext}>Review automated findings<ChevronRight className="size-4" /></Button></div>
      </div>
    </section>
  )
}

function AutomatedFindings({ seller, listing, tree, checks, onNext }: { seller: ReturnType<typeof useInvestigations>['sellers'][number]; listing: ReturnType<typeof useInvestigations>['sellers'][number]['listings'][number]; tree: TreeResult; checks: { label: string; passed: boolean; result: string }[]; onNext: () => void }) {
  return (
    <section className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
      <div className="space-y-4"><article className="surface p-6"><div className="flex items-start gap-3"><span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-peach text-brand"><Scale className="size-5" /></span><div><p className="eyebrow">Deterministic decision tree</p><h2 className="heading-5 mt-2">Result: {tree}</h2><p className="body-6 mt-2 text-muted">Five fixed checks determine this color. AI cannot change the tree outcome.</p></div></div><div className="mt-6 divide-y divide-line">{checks.map((check) => <div key={check.label} className="flex items-center gap-3 py-4"><span className={cn('flex size-8 shrink-0 items-center justify-center rounded-lg', check.passed ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700')}>{check.passed ? <CircleAlert className="size-4" /> : <CheckCircle2 className="size-4" />}</span><div className="flex-1"><p className="text-base font-semibold text-ink">{check.label}</p><p className="caption-5 text-muted">{check.result}</p></div><Badge tone={check.passed ? 'red' : 'green'}>{check.passed ? 'Flag' : 'Pass'}</Badge></div>)}</div></article><article className="surface p-6"><h2 className="heading-6">Knowledge base match</h2><div className="mt-4 grid gap-4 md:grid-cols-2"><Info label="Brand and product line" value={`${listing.category} · ${listing.title}`} /><Info label="Known capacity or model" value={listing.sku} /><Info label="Reference price range" value={`${formatCurrency(listing.marketPriceMin ?? listing.price)} to ${formatCurrency(listing.marketPriceMax ?? listing.price)}`} /><Info label="Reviews grouped by variation" value={`${seller.reports.length} related reports`} /></div></article></div>
      <aside className="space-y-4"><article className="surface p-6"><div className="flex items-center gap-3"><BrainCircuit className="size-5 text-brand" /><h2 className="heading-6">AI confidence layer</h2></div><div className="mt-5 flex items-end justify-between"><span className="text-base font-medium text-muted">Evidence confidence</span><strong className="text-4xl font-semibold tabular-nums text-ink">{seller.confidence}%</strong></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-stone-100"><div className="h-full rounded-full bg-brand" style={{ width: `${seller.confidence}%` }} /></div><h3 className="mt-6 text-base font-semibold text-ink">Why confidence is high</h3><ul className="mt-3 space-y-2 text-base text-muted"><li>• Price and visual signals agree</li><li>• {seller.reports.length > 1 ? 'Buyer reports corroborate the mismatch' : 'Buyer evidence supports the mismatch'}</li><li>• Official reference data is available</li></ul><h3 className="mt-6 text-base font-semibold text-ink">Missing evidence</h3><p className="body-6 mt-2 text-muted">Seller provenance document and serial verification are not available.</p><h3 className="mt-6 text-base font-semibold text-ink">What would change this</h3><p className="body-6 mt-2 text-muted">A verified product certificate or clearer photos could reduce the confidence score. The tree color changes only when a fixed check changes.</p></article><Button className="w-full" onClick={onNext}>Start human decision<ChevronRight className="size-4" /></Button></aside>
    </section>
  )
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: string }) { return <div className="rounded-lg bg-canvas p-4"><p className="text-sm font-medium text-muted">{label}</p><p className={cn('mt-1 text-xl font-semibold tabular-nums text-ink', tone)}>{value}</p></div> }
function SummaryRow({ label, value }: { label: string; value: string }) { return <div className="flex items-center justify-between gap-4"><dt className="text-muted">{label}</dt><dd className="font-semibold text-ink">{value}</dd></div> }
function Photo({ label, src, alt }: { label: string; src: string; alt: string }) { return <figure className="overflow-hidden rounded-xl bg-canvas"><img src={src} alt={alt} className="aspect-[4/3] w-full object-cover" /><figcaption className="p-3 text-base font-semibold text-ink">{label}</figcaption></figure> }
function Info({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-canvas p-4"><p className="text-sm font-medium text-muted">{label}</p><p className="body-2 mt-1 text-ink">{value}</p></div> }
