import { useMemo, useState } from 'react'
import { Bot, ChevronDown, ChevronUp, FileImage, Filter, Link2, MessageSquareText, ShieldCheck } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { InvestigationSubpageHeader } from '../components/investigations/InvestigationSubpageHeader'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { useInvestigations } from '../hooks/useInvestigations'
import { cn, formatDate } from '../lib/utils'

export function BuyerReportsAnalysisPage() {
  const { sellerId = '' } = useParams()
  const { getSeller } = useInvestigations()
  const seller = getSeller(sellerId)
  const [filter, setFilter] = useState('All evidence')
  const [expanded, setExpanded] = useState<string | null>(null)
  if (!seller) return <div className="page-container"><Link to="/" className="text-brand">Return to queue</Link></div>
  const reports = useMemo(() => seller.reports.filter((report) => filter === 'All evidence' || report.evidenceStatus === filter), [seller.reports, filter])
  const allFindings = seller.listings.flatMap((listing) => listing.findings)
  const mismatchCount = allFindings.filter((finding) => finding.result === 'Mismatch').length
  const avgConfidence = Math.round(allFindings.reduce((total, finding) => total + finding.confidence, 0) / allFindings.length)
  return (
    <div className="page-container">
      <InvestigationSubpageHeader seller={seller} title="Buyer reports / AI analysis" description="Review buyer complaints, attached evidence and aggregated signals before deciding the case." />
      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
        <section>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="caption-4 uppercase tracking-[0.1em] text-brand">Customer evidence</p><h2 className="heading-5 mt-1">Buyer reports</h2><p className="body-6 mt-2 text-muted">Complaints linked to the listings in this investigation.</p></div><label className="relative"><span className="sr-only">Filter evidence status</span><select className="form-control min-w-44 appearance-none pr-9" value={filter} onChange={(event) => setFilter(event.target.value)}><option>All evidence</option><option>Verified</option><option>Pending</option><option>Insufficient</option></select><Filter className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted" /></label></div>
          <div className="mt-5 space-y-3">{reports.map((report) => {
            const listing = seller.listings.find((item) => item.id === report.listingId)!
            const isOpen = expanded === report.id
            return <article key={report.id} className="surface overflow-hidden"><button className="focus-ring flex w-full items-start gap-4 p-5 text-left transition-colors duration-300 hover:bg-canvas" onClick={() => setExpanded(isOpen ? null : report.id)} aria-expanded={isOpen}><span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-peach text-brand"><MessageSquareText className="size-5" /></span><span className="min-w-0 flex-1"><span className="flex flex-wrap items-center gap-2"><strong className="title-3">{report.buyerName}</strong><Badge tone={report.evidenceStatus === 'Verified' ? 'green' : report.evidenceStatus === 'Pending' ? 'yellow' : 'red'}>{report.evidenceStatus}</Badge></span><span className="caption-5 mt-1 block text-muted">Reported {formatDate(report.reportedAt)} · {listing.title}</span><span className={cn('body-6 mt-3 block text-stone-700', !isOpen && 'line-clamp-2')}>{report.complaint}</span></span>{isOpen ? <ChevronUp className="size-5 text-muted" /> : <ChevronDown className="size-5 text-muted" />}</button>{isOpen && <div className="border-t border-line bg-[#FCFBFA] p-5"><div className="grid gap-4 sm:grid-cols-3"><div><p className="caption-4 text-muted">Report ID</p><p className="body-5 mt-1">{report.id}</p></div><div><p className="caption-4 text-muted">Attached images</p><p className="body-5 mt-1">{report.attachedImages} files</p></div><div><p className="caption-4 text-muted">Associated listing</p><p className="body-5 mt-1">{report.listingId}</p></div></div><div className="mt-4 flex flex-wrap gap-2"><Link to={`/investigations/${seller.id}/evidence?listing=${report.listingId}`}><Button size="sm" variant="outline"><FileImage className="size-4" />View attached evidence</Button></Link><Link to={`/investigations/${seller.id}/evidence?listing=${report.listingId}`}><Button size="sm" variant="ghost"><Link2 className="size-4" />Open listing comparison</Button></Link></div></div>}</article>
          })}</div>
          {reports.length === 0 && <div className="surface mt-5 p-12 text-center"><MessageSquareText className="mx-auto size-7 text-muted" /><h3 className="heading-6 mt-3">No reports in this view</h3><p className="body-6 mt-2 text-muted">Choose another evidence status to see buyer reports.</p></div>}
        </section>
        <aside className="space-y-4 xl:sticky xl:top-24 xl:self-start">
          <section className="surface p-6">
            <div className="flex items-center gap-2"><Bot className="size-5 text-brand" /><h2 className="heading-6">AI analysis</h2></div><p className="body-6 mt-2 text-muted">Aggregated from buyer reports, listing attributes, visual evidence and seller history.</p>
            <div className="mt-5 grid grid-cols-2 gap-3"><Metric label="Signal confidence" value={`${avgConfidence}%`} /><Metric label="Material mismatches" value={String(mismatchCount)} /><Metric label="Reports analyzed" value={String(seller.reports.length)} /><Metric label="Listings linked" value={String(seller.listings.length)} /></div>
            <div className="mt-5"><h3 className="title-3">Aggregated signals</h3><ul className="mt-3 space-y-3">{['Model geometry differs across independent buyer images', 'Complaint language describes the same version substitution pattern', 'Seller history includes related evidence conflicts'].map((item) => <li key={item} className="flex gap-3 text-base text-stone-700"><ShieldCheck className="mt-1 size-4 shrink-0 text-brand" />{item}</li>)}</ul></div>
          </section>
          <section className="organic-panel rounded-xl border border-[#FFD7C7] bg-peach p-6"><div className="relative z-10"><p className="caption-4 uppercase tracking-[0.1em] text-brand">AI conclusion</p><p className="body-2 mt-3 text-ink">Evidence is consistent with repeated product substitution across multiple listings.</p><p className="body-6 mt-3 text-muted">The strongest support comes from model and version mismatches. A human reviewer should confirm policy applicability and evidence provenance.</p><Link to={`/investigations/${seller.id}/decision`} className="mt-5 block"><Button className="w-full">Continue to decision</Button></Link></div></section>
        </aside>
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-canvas p-3"><p className="caption-4 text-muted">{label}</p><strong className="mt-1 block text-xl font-semibold tabular-nums">{value}</strong></div> }
