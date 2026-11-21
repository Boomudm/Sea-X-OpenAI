import { useMemo, useState, type FormEvent, type ReactNode } from 'react'
import { Camera, Link2, Upload } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useInvestigations } from '../../hooks/useInvestigations'
import { useToast } from '../ui/Toast'
import { Button } from '../ui/Button'
import { Drawer } from '../ui/Drawer'

interface AddCaseDrawerProps { open: boolean; onClose: () => void }

const splitLines = (value: string) => value.split(/\r?\n/).map((item) => item.trim()).filter(Boolean)
const isUrl = (value: string) => {
  try {
    const url = new URL(value)
    return (url.protocol === 'https:' || url.protocol === 'http:') && !url.username && !url.password
  } catch {
    return false
  }
}

export function AddCaseDrawer({ open, onClose }: AddCaseDrawerProps) {
  const { addCase } = useInvestigations()
  const { toast } = useToast()
  const navigate = useNavigate()
  const [sellerName, setSellerName] = useState('')
  const [listingLinks, setListingLinks] = useState('')
  const [referenceLinks, setReferenceLinks] = useState('')
  const [complaint, setComplaint] = useState('')
  const [currentPrice, setCurrentPrice] = useState('')
  const [previousPrice, setPreviousPrice] = useState('')
  const [photoCount, setPhotoCount] = useState(0)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const listingUrls = useMemo(() => splitLines(listingLinks), [listingLinks])
  const referenceUrls = useMemo(() => splitLines(referenceLinks), [referenceLinks])

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const nextErrors: Record<string, string> = {}
    if (!sellerName.trim()) nextErrors.sellerName = 'Enter the seller or shop name.'
    if (listingUrls.length === 0) nextErrors.listingLinks = 'Add at least one listing link.'
    else if (listingUrls.length > 10) nextErrors.listingLinks = 'Add up to 10 listing links.'
    else if (listingUrls.some((url) => !isUrl(url))) nextErrors.listingLinks = 'Every listing link must start with http or https.'
    if (referenceUrls.some((url) => !isUrl(url))) nextErrors.referenceLinks = 'Every reference link must start with http or https.'
    for (const [key, value] of [['previousPrice', previousPrice], ['currentPrice', currentPrice]]) {
      if (value && (!Number.isFinite(Number(value)) || Number(value) < 0)) nextErrors[key] = 'Enter a valid price.'
    }
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return

    const seller = addCase({
      sellerName,
      listingUrls,
      referenceUrls,
      complaint,
      currentPrice: currentPrice ? Number(currentPrice) : undefined,
      previousPrice: previousPrice ? Number(previousPrice) : undefined,
      buyerPhotoCount: photoCount,
    })
    toast(`Listing sources saved for ${seller.name}.`)
    onClose()
    const params = new URLSearchParams({ priority: 'unknown', case: seller.listings[0].id })
    navigate('/review?' + params)
  }

  return (
    <Drawer open={open} onClose={onClose} title="Add listing sources" description="Save SSD listings and reference links for evidence collection. You can enter prices and a buyer report for the first listing.">
      <form onSubmit={submit} className="space-y-6" noValidate>
        <Field label="Seller or shop name" required error={errors.sellerName}>
          <input className="form-control w-full" value={sellerName} onChange={(event) => setSellerName(event.target.value)} placeholder="Example: MajuGadget Store" />
        </Field>
        <Field label="Seller listing links" required helper={`${listingUrls.length} of 10 links captured`} error={errors.listingLinks} icon={<Link2 className="size-4" />}>
          <textarea className="form-control min-h-32 w-full resize-y py-3" value={listingLinks} onChange={(event) => setListingLinks(event.target.value)} placeholder="Paste one URL per line" />
        </Field>
        <Field label="Official Mall or brand references" helper="Optional, one URL per line" error={errors.referenceLinks} icon={<Link2 className="size-4" />}>
          <textarea className="form-control min-h-24 w-full resize-y py-3" value={referenceLinks} onChange={(event) => setReferenceLinks(event.target.value)} placeholder="Paste the official product reference" />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Previous price" helper="Price before promotion" error={errors.previousPrice}>
            <input className="form-control w-full" type="number" min="0" step="0.01" value={previousPrice} onChange={(event) => setPreviousPrice(event.target.value)} placeholder="129.90" />
          </Field>
          <Field label="Current price" helper="Displayed price now" error={errors.currentPrice}>
            <input className="form-control w-full" type="number" min="0" step="0.01" value={currentPrice} onChange={(event) => setCurrentPrice(event.target.value)} placeholder="69.90" />
          </Field>
        </div>
        <Field label="Buyer complaint or review" helper="Optional evidence for the review pattern check">
          <textarea className="form-control min-h-24 w-full resize-y py-3" value={complaint} onChange={(event) => setComplaint(event.target.value)} placeholder="Describe what the buyer received." />
        </Field>
        <label className="focus-within:ring-2 focus-within:ring-brand focus-within:ring-offset-2 block cursor-pointer rounded-xl border border-dashed border-stone-300 bg-canvas p-5 text-center hover:border-brand">
          <input type="file" multiple accept="image/*" className="sr-only" onChange={(event) => setPhotoCount(event.target.files?.length ?? 0)} />
          {photoCount ? <Camera className="mx-auto size-6 text-brand" /> : <Upload className="mx-auto size-6 text-muted" />}
          <span className="body-2 mt-2 block text-ink">{photoCount ? `${photoCount} buyer photos selected` : 'Add buyer photos'}</span>
          <span className="caption-5 mt-1 block text-muted">The demo saves the file count only.</span>
        </label>
        <div className="sticky bottom-0 flex justify-end gap-3 border-t border-line bg-white py-4">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button type="submit">Save listing sources</Button>
        </div>
      </form>
    </Drawer>
  )
}

function Field({ label, helper, required, error, icon, children }: { label: string; helper?: string; required?: boolean; error?: string; icon?: ReactNode; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-2 flex items-center gap-2 text-base font-semibold text-ink">{icon}{label}{required && <span className="text-brand" aria-hidden="true">*</span>}</span>
      {children}
      <span className={`mt-2 block text-sm ${error ? 'font-medium text-red-700' : 'text-muted'}`}>{error || helper}</span>
    </label>
  )
}
