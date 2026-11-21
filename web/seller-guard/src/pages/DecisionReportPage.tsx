import { useMemo, useState } from 'react'
import { CheckCircle2, CircleHelp, Download, FileCheck2, Printer, ShieldX } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { InvestigationSubpageHeader } from '../components/investigations/InvestigationSubpageHeader'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Dialog } from '../components/ui/Dialog'
import { useToast } from '../components/ui/Toast'
import { useInvestigations } from '../hooks/useInvestigations'
import { cn, formatDateTime } from '../lib/utils'
import type { DecisionType } from '../types'

const options: { type: DecisionType; title: string; description: string; icon: typeof ShieldX; tone: string }[] = [
  { type: 'Shortfall confirmed', title: 'Shortfall confirmed', description: 'The reviewer found a delivered capacity shortfall.', icon: ShieldX, tone: 'text-red-700 bg-red-50' },
  { type: 'Not confirmed', title: 'Not confirmed', description: 'The evidence does not confirm a delivered capacity shortfall.', icon: CheckCircle2, tone: 'text-emerald-700 bg-emerald-50' },
  { type: 'Need more information', title: 'Need more information', description: 'The record is incomplete and requires follow up.', icon: CircleHelp, tone: 'text-amber-700 bg-amber-50' },
]

export function DecisionReportPage() {
  const { sellerId = '' } = useParams()
  const { getSeller, decisions, submitDecision } = useInvestigations()
  const { toast } = useToast()
  const seller = getSeller(sellerId)
  const existing = decisions.find((decision) => decision.sellerId === sellerId)
  const [selection, setSelection] = useState<DecisionType | ''>(existing?.type ?? '')
  const [notes, setNotes] = useState(existing?.notes ?? '')
  const [error, setError] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submittedAt, setSubmittedAt] = useState(existing?.timestamp ?? '')
  const evidenceSummary = useMemo(() => seller ? seller.listings.flatMap((listing) => listing.findings).reduce((acc, finding) => ({ ...acc, [finding.result]: (acc[finding.result] ?? 0) + 1 }), {} as Record<string, number>) : {}, [seller])
  if (!seller) return <div className="page-container"><Link to="/" className="text-brand">Return to queue</Link></div>
  const validate = () => {
    if (!selection) { setError('Choose a reviewer decision before continuing.'); return }
    if (notes.trim().length < 20) { setError('Add reviewer notes with at least 20 characters.'); return }
    setError(''); setConfirmOpen(true)
  }
  const confirm = () => {
    if (!selection) return
    setSubmitting(true)
    window.setTimeout(() => {
      const decision = submitDecision(seller.id, selection, notes)
      setSubmittedAt(decision.timestamp)
      setSubmitting(false); setConfirmOpen(false)
      toast(`Decision recorded for ${seller.name}.`)
    }, 450)
  }
  const exportPdf = async () => {
    const { jsPDF } = await import('jspdf')
    const doc = new jsPDF()
    doc.setTextColor(238, 77, 45); doc.setFontSize(11); doc.text('SHOPEE TRUST & SAFETY', 20, 20)
    doc.setTextColor(33, 26, 24); doc.setFontSize(21); doc.text('Seller investigation report', 20, 34)
    doc.setDrawColor(234, 227, 223); doc.line(20, 41, 190, 41)
    const lines = [
      ['Seller', seller.name], ['Shop ID', seller.shopId], ['Risk score', `${seller.riskScore} / 100`], ['AI confidence', `${seller.confidence}%`],
      ['Buyer reports', String(seller.reports.length)], ['Listings reviewed', String(seller.listings.length)], ['Reviewer decision', selection || 'Not submitted'],
      ['Reviewer', 'Alex Morgan'], ['Decision time', submittedAt ? formatDateTime(submittedAt) : 'Not submitted'],
    ]
    let y = 52
    doc.setFontSize(10)
    lines.forEach(([label, value]) => { doc.setTextColor(120, 113, 108); doc.text(label, 20, y); doc.setTextColor(33, 26, 24); doc.text(value, 68, y); y += 9 })
    doc.setFontSize(13); doc.text('Evidence summary', 20, y + 6); y += 14
    doc.setFontSize(10); const summaryLines = doc.splitTextToSize(seller.summary, 170); doc.text(summaryLines, 20, y); y += summaryLines.length * 5 + 8
    doc.setFontSize(13); doc.text('Reviewer notes', 20, y); y += 8
    doc.setFontSize(10); doc.text(doc.splitTextToSize(notes || 'No reviewer notes have been recorded.', 170), 20, y)
    doc.setFontSize(8); doc.setTextColor(120, 113, 108); doc.text('Fictional demonstration · Human review required for all enforcement outcomes', 20, 286)
    doc.save(`${seller.shopId}-investigation-report.pdf`)
    toast('PDF report downloaded.')
  }
  return (
    <div className="page-container">
      <InvestigationSubpageHeader seller={seller} title="Decision / reports" description="Make the final reviewer decision and generate a complete investigation report." />
      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.72fr)]">
        <section className="surface p-6 no-print">
          <p className="caption-4 uppercase tracking-[0.1em] text-brand">Reviewer decision</p><h2 className="heading-5 mt-1">Record the investigation outcome</h2><p className="body-6 mt-2 text-muted">Select one outcome and explain how the evidence supports your decision.</p>
          <div className="mt-6 grid gap-3">{options.map((option) => { const Icon = option.icon; const selected = selection === option.type; return <button key={option.type} type="button" onClick={() => { setSelection(option.type); setError('') }} className={cn('focus-ring flex items-start gap-4 rounded-xl border p-4 text-left transition duration-300 ease-weighted hover:border-stone-300', selected ? 'border-brand bg-peach shadow-soft' : 'border-line bg-white')} aria-pressed={selected}><span className={cn('flex size-10 shrink-0 items-center justify-center rounded-lg', option.tone)}><Icon className="size-5" /></span><span className="flex-1"><strong className="title-3 block">{option.title}</strong><span className="body-6 mt-1 block text-muted">{option.description}</span></span><span className={cn('mt-2 size-4 rounded-full border-2', selected ? 'border-brand bg-brand ring-4 ring-orange-100' : 'border-stone-300')} /></button> })}</div>
          <label className="mt-6 block"><span className="title-4">Reviewer notes <span className="text-brand">Required</span></span><textarea className="form-control mt-2 min-h-36 w-full resize-y py-3" value={notes} onChange={(event) => { setNotes(event.target.value); setError('') }} placeholder="Explain the evidence considered, relevant policy and rationale for this outcome." /><span className="caption-5 mt-1 block text-muted">{notes.trim().length} characters · minimum 20</span></label>
          {error && <p className="body-6 mt-3 rounded-lg bg-red-50 p-3 text-red-700" role="alert">{error}</p>}
          <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end"><Button variant="outline" onClick={() => window.history.back()}>Return to evidence</Button><Button onClick={validate}>Review and confirm</Button></div>
        </section>
        <aside className="space-y-5">
          <section className="surface p-6">
            <div className="flex items-center justify-between"><div><p className="caption-4 uppercase tracking-[0.1em] text-brand">Evidence summary</p><h2 className="heading-6 mt-1">Investigation report</h2></div><FileCheck2 className="size-6 text-brand" /></div>
            <dl className="mt-5 grid grid-cols-2 gap-4"><ReportValue label="Risk score" value={`${seller.riskScore} / 100`} /><ReportValue label="AI confidence" value={`${seller.confidence}%`} /><ReportValue label="Buyer reports" value={String(seller.reports.length)} /><ReportValue label="Listings reviewed" value={String(seller.listings.length)} /></dl>
            <div className="mt-5 border-t border-line pt-5"><h3 className="title-4">Evidence findings</h3><div className="mt-3 flex flex-wrap gap-2"><Badge tone="red">{evidenceSummary.Mismatch ?? 0} mismatches</Badge><Badge tone="yellow">{evidenceSummary.Warning ?? 0} warnings</Badge><Badge tone="green">{evidenceSummary.Match ?? 0} matches</Badge></div><p className="body-6 mt-4 text-muted">{seller.summary}</p></div>
            <div className="mt-5 border-t border-line pt-5"><h3 className="title-4">Recorded outcome</h3>{submittedAt ? <div className="mt-3 rounded-lg bg-emerald-50 p-4"><p className="body-5 text-emerald-800">{selection}</p><p className="caption-5 mt-1 text-emerald-700">Recorded by Alex Morgan · {formatDateTime(submittedAt)}</p><p className="body-6 mt-3 text-emerald-900">{notes}</p></div> : <p className="body-6 mt-2 text-muted">No reviewer decision has been submitted yet.</p>}</div>
            <div className="mt-5 flex gap-2 no-print"><Button variant="outline" className="flex-1" onClick={() => window.print()}><Printer className="size-4" />Print</Button><Button variant="outline" className="flex-1" onClick={exportPdf}><Download className="size-4" />Export PDF</Button></div>
          </section>
        </aside>
      </div>
      <Dialog open={confirmOpen} onClose={() => !submitting && setConfirmOpen(false)} title="Confirm reviewer decision" description="This outcome will update the investigation status and appear in decision history."><div className="rounded-lg bg-canvas p-4"><p className="caption-4 text-muted">Selected outcome</p><p className="title-3 mt-1">{selection}</p><p className="body-6 mt-3 text-muted">{notes}</p></div><div className="mt-5 flex justify-end gap-2"><Button variant="ghost" disabled={submitting} onClick={() => setConfirmOpen(false)}>Go back</Button><Button loading={submitting} onClick={confirm}>Confirm decision</Button></div></Dialog>
    </div>
  )
}

function ReportValue({ label, value }: { label: string; value: string }) { return <div><dt className="caption-4 text-muted">{label}</dt><dd className="title-3 mt-1 tabular-nums">{value}</dd></div> }
