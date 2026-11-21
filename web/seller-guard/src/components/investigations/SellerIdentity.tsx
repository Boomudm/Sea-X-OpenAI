import type { Seller } from '../../types'

export function SellerIdentity({ seller, showId = false }: { seller: Seller; showId?: boolean }) {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <span className="flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-peach text-xs font-semibold text-brand"><img src={seller.listings[0].advertisedImage} alt="" className="size-full object-cover mix-blend-multiply" /></span>
      <span className="min-w-0"><strong className="block truncate text-base font-semibold text-ink">{seller.name}</strong>{showId && <span className="block text-sm text-muted">{seller.shopId}</span>}</span>
    </div>
  )
}
