import { useMemo, useState } from 'react'
import { ChevronDown, Search } from 'lucide-react'
import { Link } from 'react-router-dom'
import { PageHeader } from '../components/layout/PageHeader'
import { SellerIdentity } from '../components/investigations/SellerIdentity'
import { Badge } from '../components/ui/Badge'
import { useInvestigations } from '../hooks/useInvestigations'
import { formatDateTime } from '../lib/utils'

export function DecisionHistoryPage() {
  const { decisions, getSeller } = useInvestigations()
  const [query, setQuery] = useState('')
  const [outcome, setOutcome] = useState('All outcomes')
  const visible = useMemo(() => decisions.filter((decision) => {
    const seller = getSeller(decision.sellerId)
    return seller && `${seller.name} ${seller.shopId} ${decision.notes}`.toLowerCase().includes(query.toLowerCase()) && (outcome === 'All outcomes' || decision.type === outcome)
  }).sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp)), [decisions, getSeller, query, outcome])
  return (
    <div className="page-container">
      <PageHeader eyebrow="Audit trail" title="Decision history" description="Review completed outcomes, supporting notes and the reviewer responsible for each decision." />
      <div className="mt-8 flex flex-col gap-3 sm:flex-row"><div className="relative flex-1 sm:max-w-lg"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" /><input className="form-control w-full pl-9" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search seller, Shop ID or notes" /></div><label className="relative"><select className="form-control min-w-52 appearance-none pr-9" value={outcome} onChange={(event) => setOutcome(event.target.value)}><option>All outcomes</option><option>Shortfall confirmed</option><option>Not confirmed</option><option>Need more information</option></select><ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-muted" /></label></div>
      <section className="surface mt-5 overflow-hidden">
        {visible.length ? <div className="overflow-x-auto"><table className="w-full min-w-[960px] text-left"><thead className="bg-[#FCFBFA]"><tr>{['Seller', 'Outcome', 'Reviewer notes', 'Reviewer', 'Recorded'].map((label) => <th key={label} className="border-b border-line px-5 py-3 text-sm font-semibold text-muted">{label}</th>)}</tr></thead><tbody>{visible.map((decision) => { const seller = getSeller(decision.sellerId)!; return <tr key={`${decision.sellerId}-${decision.timestamp}`} className="hover:bg-peach/40"><td className="border-b border-line p-5"><Link className="focus-ring rounded" to={`/investigations/${seller.id}/decision`}><SellerIdentity seller={seller} showId /></Link></td><td className="border-b border-line p-5"><Badge tone={decision.type === 'Shortfall confirmed' ? 'red' : decision.type === 'Not confirmed' ? 'green' : 'yellow'}>{decision.type}</Badge></td><td className="max-w-sm border-b border-line p-5 text-base text-muted"><span className="line-clamp-2">{decision.notes}</span></td><td className="border-b border-line p-5 text-base font-medium">{decision.reviewer}</td><td className="whitespace-nowrap border-b border-line p-5 text-base text-muted">{formatDateTime(decision.timestamp)}</td></tr> })}</tbody></table></div> : <div className="p-16 text-center"><h2 className="heading-6">No decisions in this view</h2><p className="body-6 mt-2 text-muted">Submitted reviewer outcomes will appear here. Adjust the search or outcome filter if needed.</p></div>}
      </section>
    </div>
  )
}
