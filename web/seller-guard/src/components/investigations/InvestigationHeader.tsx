import { ChevronRight, Flag, ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Seller } from '../../types'
import { Badge } from '../ui/Badge'
import { RiskScore } from './RiskScore'
import { SellerIdentity } from './SellerIdentity'

export function InvestigationHeader({ seller }: { seller: Seller }) {
  return (
    <>
      <nav className="mb-5 flex items-center gap-1.5 text-base text-muted" aria-label="Breadcrumb">
        <Link to="/" className="focus-ring rounded hover:text-ink">Review queue</Link><ChevronRight className="size-4" /><span className="truncate text-ink">{seller.name}</span>
      </nav>
      <section className="surface organic-panel">
        <div className="grid gap-0 lg:grid-cols-[220px_minmax(0,1fr)]">
          <div className="relative min-h-52 overflow-hidden bg-peach lg:min-h-56">
            <div className="absolute -left-10 top-4 size-48 rotate-[-12deg] rounded-full bg-[#FFDCCC]" />
            <img src={seller.listings[0].advertisedImage} alt={`${seller.listings[0].title} from ${seller.name}`} className="relative z-10 size-full min-h-52 object-cover mix-blend-multiply lg:min-h-56" />
          </div>
          <div className="relative z-10 flex flex-col justify-between gap-6 p-6 lg:p-8">
            <div>
              <div className="flex flex-wrap items-center gap-2"><h1 className="heading-2">{seller.name}</h1><Badge tone="orange"><Flag className="mr-1 size-3" />AI flagged</Badge><Badge tone={seller.status === 'Resolved' ? 'green' : seller.status === 'In progress' ? 'blue' : 'neutral'}>{seller.status}</Badge></div>
              <p className="body-6 mt-2 text-muted">Shop ID {seller.shopId} · {seller.listingsCount} listings analyzed · {seller.category}</p>
            </div>
            <div className="grid grid-cols-2 divide-x divide-line rounded-xl border border-line bg-white/80 p-4 backdrop-blur-sm sm:grid-cols-3">
              <div className="px-3"><p className="caption-4 text-muted">Risk score</p><div className="mt-1 text-2xl"><RiskScore score={seller.riskScore} compact /></div></div>
              <div className="px-3"><p className="caption-4 text-muted">AI confidence</p><strong className="mt-1 block text-2xl font-semibold tabular-nums">{seller.confidence}%</strong></div>
              <div className="col-span-2 mt-4 border-t border-line px-3 pt-4 sm:col-span-1 sm:mt-0 sm:border-t-0 sm:pt-0"><p className="caption-4 text-muted">Recommendation</p><strong className="mt-1 flex items-center gap-1.5 text-base font-semibold"><ShieldAlert className="size-4 text-brand" />{seller.recommendation}</strong></div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
