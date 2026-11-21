import { useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, CheckCircle2, Expand, ImageIcon, X, XCircle, ZoomIn } from 'lucide-react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { InvestigationSubpageHeader } from '../components/investigations/InvestigationSubpageHeader'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { useInvestigations } from '../hooks/useInvestigations'
import { cn, formatCurrency } from '../lib/utils'

export function EvidenceComparisonPage() {
  const { sellerId = '' } = useParams()
  const { getSeller } = useInvestigations()
  const seller = getSeller(sellerId)
  const [searchParams] = useSearchParams()
  const requestedListing = searchParams.get('listing')
  const requestedIndex = seller?.listings.findIndex((listing) => listing.id === requestedListing) ?? -1
  const [activeIndex, setActiveIndex] = useState(requestedIndex >= 0 ? requestedIndex : 0)
  const [lightbox, setLightbox] = useState<string | null>(null)
  useEffect(() => {
    if (!lightbox) return
    const close = (event: KeyboardEvent) => event.key === 'Escape' && setLightbox(null)
    document.addEventListener('keydown', close)
    return () => document.removeEventListener('keydown', close)
  }, [lightbox])
  useEffect(() => {
    if (requestedIndex >= 0) setActiveIndex(requestedIndex)
  }, [requestedIndex])
  if (!seller) return <div className="page-container"><Link to="/" className="text-brand">Return to queue</Link></div>
  const listing = seller.listings[activeIndex]
  const move = (direction: number) => setActiveIndex((current) => (current + direction + seller.listings.length) % seller.listings.length)
  return (
    <div className="page-container">
      <InvestigationSubpageHeader seller={seller} title="Evidence comparison" description="Compare the advertised item with the product reported and received by the buyer." />
      <div className="mt-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div><p className="eyebrow">Visual evidence</p><h2 className="heading-6 mt-1">Advertised and received item</h2></div>
        <div className="flex items-center gap-2"><Button variant="outline" size="icon" onClick={() => move(-1)} aria-label="Previous listing"><ArrowLeft className="size-4" /></Button><span className="min-w-20 text-center text-base font-medium">{activeIndex + 1} of {seller.listings.length}</span><Button variant="outline" size="icon" onClick={() => move(1)} aria-label="Next listing"><ArrowRight className="size-4" /></Button></div>
      </div>
      <div className="mt-5 flex gap-3 overflow-x-auto pb-2" role="tablist" aria-label="Evidence listings">
        {seller.listings.map((item, index) => <button key={item.id} role="tab" aria-selected={index === activeIndex} onClick={() => setActiveIndex(index)} className={cn('focus-ring flex min-w-72 items-center gap-3 rounded-xl border bg-white p-3 text-left transition-colors duration-300', index === activeIndex ? 'border-brand shadow-soft' : 'border-line hover:border-stone-300')}><img className="size-14 rounded-lg object-cover" src={item.advertisedImage} alt="" /><span className="min-w-0"><strong className="block truncate text-base font-semibold">{item.title}</strong><span className="mt-1 block text-sm text-muted">{item.id}</span></span></button>)}
      </div>
      <div className="mt-4 grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="grid gap-4 md:grid-cols-2" aria-label="Image comparison">
          <EvidenceImage label="Advertised listing image" image={listing.advertisedImage} alt={`Advertised ${listing.title}`} badge="Seller listing" onOpen={() => setLightbox(listing.advertisedImage)} />
          <EvidenceImage label="Buyer received item" image={listing.receivedImage} alt={`Buyer received item for ${listing.title}`} badge="Buyer evidence" onOpen={() => setLightbox(listing.receivedImage)} warning />
          <div className="surface p-5 md:col-span-2">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><p className="caption-4 text-muted">Evidence metadata</p><h3 className="title-2 mt-1">{listing.title}</h3></div><Badge tone="red">Material discrepancy</Badge></div>
            <div className="mt-5 grid gap-4 sm:grid-cols-4"><Meta label="Listing ID" value={listing.id} /><Meta label="SKU" value={listing.sku} /><Meta label="Category" value={listing.category} /><Meta label="Listed price" value={formatCurrency(listing.price)} /></div>
            <div className="mt-5 rounded-lg bg-red-50 p-4"><p className="body-5 text-red-800">Highlighted discrepancy</p><p className="body-6 mt-1 text-red-700">{listing.discrepancy}</p></div>
          </div>
        </section>
        <aside className="surface h-fit p-5 xl:sticky xl:top-24">
          <div className="flex items-center gap-2"><ImageIcon className="size-5 text-brand" /><h2 className="heading-6">AI findings</h2></div>
          <p className="body-6 mt-2 text-muted">Computer vision findings for this evidence pair. Validate each signal against the full record.</p>
          <div className="mt-5 space-y-3">{listing.findings.map((finding) => <div key={finding.label} className="rounded-lg border border-line p-4"><div className="flex items-start gap-3">{finding.result === 'Match' ? <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-600" /> : finding.result === 'Mismatch' ? <XCircle className="mt-0.5 size-5 shrink-0 text-red-600" /> : <span className="mt-1 size-3 shrink-0 rounded-full bg-amber-500" />}<div className="min-w-0 flex-1"><div className="flex items-start justify-between gap-2"><h3 className="body-5 text-ink">{finding.label}</h3><span className="caption-4 text-muted">{finding.confidence}%</span></div><p className="caption-5 mt-1 text-muted">{finding.detail}</p><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-stone-100"><div className={cn('h-full rounded-full', finding.result === 'Match' ? 'bg-emerald-600' : finding.result === 'Mismatch' ? 'bg-red-600' : 'bg-amber-500')} style={{ width: `${finding.confidence}%` }} /></div></div></div></div>)}</div>
          <Link to={`/investigations/${seller.id}/analysis`} className="mt-5 block"><Button className="w-full">Review buyer reports<ArrowRight className="size-4" /></Button></Link>
        </aside>
      </div>
      {lightbox && <div className="fixed inset-0 z-[90] flex items-center justify-center bg-ink/90 p-4" role="dialog" aria-modal="true" aria-label="Evidence image preview" onClick={() => setLightbox(null)}><button className="focus-ring absolute right-5 top-5 rounded-lg bg-white/10 p-2 text-white hover:bg-white/20" onClick={() => setLightbox(null)} aria-label="Close image preview"><X className="size-6" /></button><img src={lightbox} alt="Expanded evidence" className="max-h-[88vh] max-w-[94vw] rounded-xl object-contain shadow-float" onClick={(event) => event.stopPropagation()} /></div>}
    </div>
  )
}

function EvidenceImage({ label, image, alt, badge, onOpen, warning = false }: { label: string; image: string; alt: string; badge: string; onOpen: () => void; warning?: boolean }) {
  return <article className="surface overflow-hidden"><div className="flex items-center justify-between p-4"><div><p className="caption-4 text-muted">{label}</p><Badge tone={warning ? 'red' : 'neutral'} className="mt-2">{badge}</Badge></div><Button variant="ghost" size="icon" onClick={onOpen} aria-label={`Expand ${label}`}><Expand className="size-4" /></Button></div><button onClick={onOpen} className="group relative block aspect-square w-full overflow-hidden bg-stone-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand"><img src={image} alt={alt} className="size-full object-cover transition-transform duration-500 ease-weighted group-hover:scale-[1.03]" /><span className="absolute bottom-4 right-4 flex items-center gap-2 rounded-lg bg-ink/80 px-3 py-2 text-sm font-semibold text-white opacity-0 backdrop-blur-sm transition-opacity duration-300 group-hover:opacity-100 group-focus:opacity-100"><ZoomIn className="size-4" />View larger</span></button></article>
}

function Meta({ label, value }: { label: string; value: string }) { return <div><p className="caption-4 text-muted">{label}</p><p className="body-5 mt-1 text-ink">{value}</p></div> }
