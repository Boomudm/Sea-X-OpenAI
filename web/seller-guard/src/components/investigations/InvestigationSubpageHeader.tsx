import { ArrowLeft, ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Seller } from '../../types'

export function InvestigationSubpageHeader({ seller, title, description }: { seller: Seller; title: string; description: string }) {
  return (
    <header>
      <nav className="mb-5 flex items-center gap-2 text-base text-muted" aria-label="Breadcrumb">
        <Link to={`/investigations/${seller.id}`} className="focus-ring flex items-center gap-1 rounded hover:text-ink"><ArrowLeft className="size-4" />Back to investigation</Link>
        <ChevronRight className="size-4" />
        <span className="truncate text-ink">{seller.name}</span>
      </nav>
      <div className="max-w-3xl">
        <h1 className="heading-2">{title}</h1>
        <p className="body-3 mt-2 text-muted">{description}</p>
      </div>
    </header>
  )
}
