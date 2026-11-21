import { CalendarDays, ChevronRight, ClipboardList, FileSearch, Info, Layers3, MapPin, PackageCheck, ShieldAlert } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { InvestigationHeader } from '../components/investigations/InvestigationHeader'
import { InvestigationNav } from '../components/investigations/InvestigationNav'
import { Button } from '../components/ui/Button'
import { useInvestigations } from '../hooks/useInvestigations'
import { formatDate } from '../lib/utils'
import { useToast } from '../components/ui/Toast'

export function InvestigationOverviewPage() {
  const { sellerId = '' } = useParams()
  const { getSeller, requestInformation } = useInvestigations()
  const { toast } = useToast()
  const navigate = useNavigate()
  const seller = getSeller(sellerId)
  if (!seller) return <MissingCase />
  const requestMore = () => {
    requestInformation(seller.id)
    toast(`Information request recorded for ${seller.name}.`)
  }
  const signals = [
    ['Product image mismatch', `${seller.listings.length} listings show visual differences between advertised and received items.`, FileSearch],
    ['Repeated buyer complaints', `${seller.reports.length} related reports were submitted across the last twelve days.`, ClipboardList],
    ['Inconsistent attributes', 'Model, color and version claims conflict with buyer supplied evidence.', Layers3],
    ['Suspicious historical pattern', `${seller.previousInvestigations} previous investigations include similar substitution concerns.`, ShieldAlert],
  ]
  return (
    <div className="page-container">
      <InvestigationHeader seller={seller} />
      <div className="mt-4"><InvestigationNav /></div>
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <div className="space-y-6">
          <section className="surface p-6">
            <div className="flex items-center gap-2"><Info className="size-5 text-brand" /><h2 className="heading-6">Investigation summary</h2></div>
            <p className="body-3 mt-4 max-w-4xl text-stone-700">{seller.summary}</p>
            <div className="mt-5 rounded-lg bg-peach p-4"><p className="caption-4 uppercase tracking-[0.1em] text-brand">Human review required</p><p className="body-6 mt-1 text-[#6E2A1C]">The AI recommendation helps prioritize evidence. It does not make or enforce the final decision.</p></div>
          </section>
          <section>
            <div className="mb-4 flex items-end justify-between"><div><p className="caption-4 text-brand">Priority evidence</p><h2 className="heading-6 mt-1">Key investigation signals</h2></div><Link className="focus-ring hidden items-center gap-1 rounded text-base font-semibold text-brand sm:flex" to={`/investigations/${seller.id}/evidence`}>View all evidence<ChevronRight className="size-4" /></Link></div>
            <div className="grid gap-3 sm:grid-cols-2">{signals.map(([title, detail, Icon]) => <div key={String(title)} className="surface p-5"><Icon className="size-5 text-brand" /><h3 className="title-3 mt-4">{title as string}</h3><p className="body-6 mt-2 text-muted">{detail as string}</p></div>)}</div>
          </section>
        </div>
        <aside className="space-y-6">
          <section className="surface p-6">
            <h2 className="heading-6">Seller at a glance</h2>
            <dl className="mt-5 space-y-4">
              {[
                [CalendarDays, 'Account created', formatDate(seller.createdAt)],
                [PackageCheck, 'Active listings', String(seller.listingsCount)],
                [Layers3, 'Primary category', seller.category],
                [MapPin, 'Fulfillment', seller.fulfillment],
                [ClipboardList, 'Previous investigations', String(seller.previousInvestigations)],
              ].map(([Icon, label, value]) => <div key={String(label)} className="flex items-start gap-3"><Icon className="mt-0.5 size-4 shrink-0 text-muted" /><div><dt className="caption-4 text-muted">{label as string}</dt><dd className="body-5 mt-0.5 text-ink">{value as string}</dd></div></div>)}
            </dl>
          </section>
          <section className="surface p-6">
            <h2 className="heading-6">Next action</h2><p className="body-6 mt-2 text-muted">Review evidence before recording a decision. Request documentation when the record is incomplete.</p>
            <div className="mt-5 flex flex-col gap-2"><Button onClick={() => navigate(`/investigations/${seller.id}/evidence`)}><FileSearch className="size-4" />Review evidence</Button><Button variant="outline" onClick={() => navigate(`/investigations/${seller.id}/decision`)}>Make decision</Button><Button variant="ghost" onClick={requestMore}>Request more information</Button></div>
          </section>
        </aside>
      </div>
    </div>
  )
}

function MissingCase() {
  return <div className="page-container"><div className="surface p-12 text-center"><h1 className="heading-5">Investigation not found</h1><p className="body-6 mt-2 text-muted">This case may have been removed or the link may be incorrect.</p><Link className="mt-5 inline-block text-base font-semibold text-brand" to="/">Return to review queue</Link></div></div>
}
