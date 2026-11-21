import { ArrowUpRight, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageHeader } from '../components/layout/PageHeader'
import { RiskScore } from '../components/investigations/RiskScore'
import { SellerIdentity } from '../components/investigations/SellerIdentity'
import { Badge } from '../components/ui/Badge'
import { useInvestigations } from '../hooks/useInvestigations'
import { formatDate } from '../lib/utils'

export function InvestigationsPage() {
  const { sellers } = useInvestigations()
  const [query, setQuery] = useState('')
  const visible = useMemo(() => sellers.filter((seller) => `${seller.name} ${seller.shopId} ${seller.keySignal}`.toLowerCase().includes(query.toLowerCase())), [sellers, query])
  return (
    <div className="page-container">
      <PageHeader eyebrow="Case workspace" title="All investigations" description="Follow active investigations from first review through evidence validation and final outcome." />
      <div className="relative mt-8 max-w-lg"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" /><input className="form-control w-full pl-9" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search investigations" /></div>
      <section className="mt-5 grid gap-4 lg:grid-cols-2">
        {visible.map((seller) => (
          <Link key={seller.id} to={`/investigations/${seller.id}`} className="surface focus-ring group p-5 transition duration-300 ease-weighted hover:-translate-y-0.5 hover:border-stone-300 hover:shadow-float">
            <div className="flex items-start justify-between gap-4"><SellerIdentity seller={seller} showId /><ArrowUpRight className="size-5 text-muted transition-colors group-hover:text-brand" /></div>
            <div className="mt-5 grid grid-cols-3 gap-3 border-t border-line pt-4">
              <div><p className="caption-4 text-muted">Risk</p><div className="mt-1"><RiskScore score={seller.riskScore} compact /></div></div>
              <div><p className="caption-4 text-muted">Status</p><div className="mt-1"><Badge tone={seller.status === 'Resolved' ? 'green' : seller.status === 'In progress' ? 'blue' : 'orange'}>{seller.status}</Badge></div></div>
              <div><p className="caption-4 text-muted">Updated</p><p className="body-5 mt-1">{formatDate(seller.lastUpdated)}</p></div>
            </div>
            <p className="body-6 mt-4 text-muted"><span className="font-medium text-ink">Key signal:</span> {seller.keySignal}</p>
          </Link>
        ))}
      </section>
      {visible.length === 0 && <div className="surface mt-5 p-12 text-center"><Search className="mx-auto size-7 text-muted" /><h2 className="heading-6 mt-3">No matching investigations</h2><p className="body-6 mt-2 text-muted">Try a seller name, Shop ID or signal.</p></div>}
    </div>
  )
}
