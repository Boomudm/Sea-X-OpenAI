import { ArrowUpRight, Bot, ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { PageHeader } from '../components/layout/PageHeader'
import { RiskScore } from '../components/investigations/RiskScore'
import { SellerIdentity } from '../components/investigations/SellerIdentity'
import { Badge } from '../components/ui/Badge'
import { useInvestigations } from '../hooks/useInvestigations'

export function AIAnalysisHubPage() {
  const { sellers } = useInvestigations()
  const priority = sellers.filter((seller) => seller.status !== 'Resolved').sort((a, b) => b.riskScore - a.riskScore).slice(0, 8)
  return (
    <div className="page-container">
      <PageHeader eyebrow="Decision support" title="AI analysis workspace" description="Review aggregated evidence signals while keeping the final enforcement decision with a trained human reviewer." />
      <section className="organic-panel mt-8 rounded-xl border border-line bg-white/90 p-6 shadow-soft md:p-8">
        <div className="relative z-10 max-w-3xl"><Bot className="size-7 text-brand" /><h2 className="heading-3 mt-5">Evidence patterns, explained with context.</h2><p className="body-3 mt-3 text-muted">Recommendations combine complaint similarity, visual discrepancies and account history. Confidence measures evidence consistency, not certainty of a policy violation.</p></div>
      </section>
      <section className="mt-8"><div className="mb-4 flex items-end justify-between"><div><p className="caption-4 uppercase tracking-[0.1em] text-brand">Priority review</p><h2 className="heading-6 mt-1">Strongest active signals</h2></div><Badge tone="orange">{priority.length} cases</Badge></div>
        <div className="surface overflow-hidden divide-y divide-line">{priority.map((seller) => <Link key={seller.id} to={`/investigations/${seller.id}/analysis`} className="focus-ring group grid gap-4 p-5 transition-colors duration-300 hover:bg-peach/40 md:grid-cols-[minmax(220px,1fr)_180px_200px_48px] md:items-center"><SellerIdentity seller={seller} showId /><div><p className="caption-4 text-muted">Key signal</p><p className="body-5 mt-1">{seller.keySignal}</p></div><div><p className="caption-4 text-muted">Risk and confidence</p><div className="mt-1 flex items-center gap-3"><RiskScore score={seller.riskScore} compact /><span className="text-sm text-muted">{seller.confidence}% confidence</span></div></div><span className="flex size-10 items-center justify-center rounded-lg text-muted group-hover:bg-white group-hover:text-brand"><ArrowUpRight className="size-5" /></span></Link>)}</div>
      </section>
      <div className="mt-6 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4"><ShieldAlert className="mt-0.5 size-5 shrink-0 text-amber-700" /><p className="body-6 text-amber-900"><strong>Reviewer accountability:</strong> AI recommendations are decision support only. Validate provenance, context and policy applicability before recording an outcome.</p></div>
    </div>
  )
}
