import type { BuyerReport, Listing, Seller } from '../types'

const samplePhoto = `data:image/svg+xml,${encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect width="400" height="300" fill="#F6F3EF"/><text x="200" y="150" fill="#57534E" text-anchor="middle" dominant-baseline="middle" font-family="sans-serif" font-size="24">Sample · No photo</text></svg>',
)}`

const samples = [
  {
    capacity: 64,
    was: 249,
    now: 219,
    marketMin: 199,
    marketMax: 249,
    signal: 'Measured capacity shortfall',
    quote: 'My write and verify test stopped after 29 GB.',
    detail: 'One sample buyer reported a measured shortfall for this exact variant.',
    confidence: 70,
  },
  {
    capacity: 128,
    was: 399,
    now: 279,
    marketMin: 299,
    marketMax: 399,
    signal: 'Low price',
    quote: 'The package says 128 GB.',
    detail: 'The sample current price is below the reference range.',
    confidence: 60,
  },
  {
    capacity: 256,
    was: 549,
    now: 499,
    marketMin: 429,
    marketMax: 549,
    signal: 'Capacity complaint needs a usable measurement',
    quote: 'The drive seems smaller than the option I bought.',
    detail: 'The sample buyer did not report a measured capacity.',
    confidence: 60,
  },
]

const shopNumber = (index: number) => String(index + 1).padStart(2, '0')

function buildListings(sellerIndex: number): Listing[] {
  return samples.map((_, offset) => {
    const sample = samples[(sellerIndex + offset) % samples.length]
    const id = `LST-${String(sellerIndex + 1).padStart(3, '0')}-${offset + 1}`
    return {
      id,
      sku: `SAMPLE-${shopNumber(sellerIndex)}-${sample.capacity}`,
      title: `Sample USB flash drive ${sample.capacity} GB`,
      category: 'USB flash drives',
      price: sample.now,
      previousPrice: sample.was,
      marketPriceMin: sample.marketMin,
      marketPriceMax: sample.marketMax,
      listingUrl: `https://example.invalid/listings/${id.toLowerCase()}`,
      referenceUrl: `https://example.invalid/reference/usb-flash-drive-${sample.capacity}gb`,
      advertisedImage: samplePhoto,
      receivedImage: samplePhoto,
      discrepancy: sample.detail,
      findings: [{
        label: sample.signal,
        result: 'Warning',
        detail: sample.detail,
        confidence: sample.confidence,
      }],
    }
  })
}

function buildReports(sellerIndex: number, listings: Listing[]): BuyerReport[] {
  return listings.map((listing, offset) => ({
    id: `RPT-${String(sellerIndex + 1).padStart(3, '0')}-${offset + 1}`,
    buyerName: `Sample buyer **${offset + 1}`,
    reportedAt: new Date(Date.UTC(2026, 10, 18 - ((sellerIndex + offset) % 12), 4 + offset, 25)).toISOString(),
    listingId: listing.id,
    complaint: samples[(sellerIndex + offset) % samples.length].quote,
    attachedImages: 0,
    evidenceStatus: 'Pending',
  }))
}

export const sellers: Seller[] = Array.from({ length: 20 }, (_, index) => {
  const sample = samples[index % samples.length]
  const listings = buildListings(index)
  const reports = buildReports(index, listings)
  return {
    id: `seller-${index + 1}`,
    name: `Sample shop ${shopNumber(index)}`,
    shopId: `SAMPLE-${shopNumber(index)}`,
    initials: 'SS',
    recommendation: 'Need more information',
    riskScore: 60,
    confidence: sample.confidence,
    keySignal: sample.signal,
    status: 'To review',
    lastUpdated: new Date(Date.UTC(2026, 10, 20 - (index % 9), 2 + (index % 7), 15)).toISOString(),
    createdAt: new Date(Date.UTC(2023 + (index % 3), (index * 3) % 12, 4 + (index % 20))).toISOString(),
    listingsCount: listings.length,
    category: 'USB flash drives',
    fulfillment: 'Sample listing',
    previousInvestigations: 0,
    summary: 'Sample data for practicing USB flash drive review. The reviewer records the verdict.',
    listings,
    reports,
  }
})

export const outcomeData = [
  { name: 'Shortfall confirmed', value: 0, color: '#EE4D2D' },
  { name: 'Not confirmed', value: 0, color: '#2F7D67' },
  { name: 'Need more information', value: 0, color: '#D99022' },
]

export const weeklyData = [12, 19].map((day) => ({
  week: `${day} Nov`,
  investigations: sellers.filter((seller) => {
    const updated = Date.parse(seller.lastUpdated)
    return updated >= Date.UTC(2026, 10, day) && updated < Date.UTC(2026, 10, day + 7)
  }).length,
  resolved: 0,
}))
