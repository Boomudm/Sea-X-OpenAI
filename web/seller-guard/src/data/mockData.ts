import type { BuyerReport, Listing, Seller } from '../types'

const products = [
  {
    title: 'AirFlex Pro wireless earbuds', category: 'Electronics', price: 69.9,
    advertisedImage: 'https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=1200&q=85',
    receivedImage: 'https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?auto=format&fit=crop&w=1200&q=85',
    discrepancy: 'The received charging case and earbud profile differ from the advertised Pro model.',
  },
  {
    title: 'Pulse S8 smart watch', category: 'Wearables', price: 84.5,
    advertisedImage: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=1200&q=85',
    receivedImage: 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=1200&q=85',
    discrepancy: 'Buyer evidence shows an older casing and a different sensor layout.',
  },
  {
    title: 'CloudStep running trainers', category: 'Fashion', price: 58.8,
    advertisedImage: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1200&q=85',
    receivedImage: 'https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=1200&q=85',
    discrepancy: 'Material, sole pattern and delivered color do not match the listing photographs.',
  },
  {
    title: 'Urban Carry commuter backpack', category: 'Bags', price: 42.9,
    advertisedImage: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=1200&q=85',
    receivedImage: 'https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?auto=format&fit=crop&w=1200&q=85',
    discrepancy: 'The received bag has fewer compartments and uses a visibly different fabric.',
  },
  {
    title: 'Glow Ritual renewal set', category: 'Beauty', price: 76.2,
    advertisedImage: 'https://images.unsplash.com/photo-1556228578-8c89e6adf883?auto=format&fit=crop&w=1200&q=85',
    receivedImage: 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=1200&q=85',
    discrepancy: 'Packaging, label alignment and product volume differ from the advertised set.',
  },
  {
    title: 'Frame Mini mirrorless camera', category: 'Cameras', price: 219.0,
    advertisedImage: 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=1200&q=85',
    receivedImage: 'https://images.unsplash.com/photo-1606980707986-e4bb0ad280f6?auto=format&fit=crop&w=1200&q=85',
    discrepancy: 'The received unit is an older camera model with a lower resolution sensor.',
  },
]

const shops = [
  ['Orchid Digital', 'Product image mismatch'],
  ['Northstar Market', 'Repeated model complaints'],
  ['Everyday Vault', 'Inconsistent listing attributes'],
  ['Aster Living', 'Suspicious historical pattern'],
  ['Urban Kind Co', 'Color and material mismatch'],
  ['Pixel Harbor', 'Unverified brand claims'],
  ['Mori Essentials', 'High complaint velocity'],
  ['BrightCart Studio', 'Description evidence conflict'],
  ['Nimble Goods', 'Version substitution'],
  ['Sage & Circuit', 'Duplicate buyer evidence'],
  ['Citrine Outlet', 'Fulfillment origin conflict'],
  ['Kinship Supply', 'Product serial mismatch'],
  ['Lumen House', 'Repeated refund requests'],
  ['Tempo Street', 'Listing photo reuse'],
  ['Copper Lane', 'Material quality mismatch'],
  ['Vela Commerce', 'Category policy conflict'],
  ['Sunday Standard', 'Incomplete product labeling'],
  ['Arc & Alder', 'Unusual account behavior'],
  ['Mango District', 'Buyer report cluster'],
  ['Kitefield Select', 'Low evidence consistency'],
]

const complaintTexts = [
  'The item delivered is not the model shown in the listing. The controls and packaging are different.',
  'I ordered the current version but received an older item without the advertised features.',
  'The color and material are visibly different from every product photo in the listing.',
  'The product label looks altered and the serial number could not be verified with the manufacturer.',
]

function buildListings(sellerIndex: number): Listing[] {
  return [0, 1, 2].map((offset) => {
    const product = products[(sellerIndex + offset) % products.length]
    const severity = (sellerIndex + offset) % 3
    return {
      id: `LST-${String(sellerIndex + 1).padStart(3, '0')}-${offset + 1}`,
      sku: `SKU-${(sellerIndex + 13) * 73 + offset * 11}`,
      ...product,
      previousPrice: Number((product.price * (1.35 + offset * 0.08)).toFixed(2)),
      marketPriceMin: Number((product.price * 1.12).toFixed(2)),
      marketPriceMax: Number((product.price * 1.78).toFixed(2)),
      listingUrl: `https://shopee.sg/product/${83649102 + sellerIndex * 7913}/${10012001 + sellerIndex * 97 + offset}`,
      referenceUrl: `https://shopee.sg/mall/reference/${product.category.toLowerCase()}/${1001 + sellerIndex + offset}`,
      findings: [
        {
          label: 'Product and model match', result: severity === 2 ? 'Match' : 'Mismatch',
          detail: severity === 2 ? 'Core silhouette and model identifiers align.' : 'Model geometry and identifier placement do not align.',
          confidence: 94 - severity * 3,
        },
        {
          label: 'Color consistency', result: severity === 1 ? 'Match' : 'Warning',
          detail: severity === 1 ? 'Color appears consistent across lighting conditions.' : 'Color variance exceeds the expected lighting tolerance.',
          confidence: 88 + severity * 2,
        },
        {
          label: 'Version consistency', result: severity === 2 ? 'Warning' : 'Mismatch',
          detail: 'Packaging and hardware details indicate a different production version.',
          confidence: 91 - severity,
        },
        {
          label: 'Listing description', result: severity === 0 ? 'Mismatch' : 'Warning',
          detail: 'Two advertised attributes are not visible in the buyer supplied evidence.',
          confidence: 86 + severity * 3,
        },
      ],
    }
  })
}

function buildReports(sellerIndex: number, listings: Listing[]): BuyerReport[] {
  return [0, 1, 2].map((offset) => ({
    id: `RPT-${String(sellerIndex + 1).padStart(3, '0')}-${offset + 1}`,
    buyerName: ['Nadia Lim', 'Ethan Wong', 'Mei Tan', 'Arun Patel'][(sellerIndex + offset) % 4],
    reportedAt: new Date(Date.UTC(2026, 10, 18 - ((sellerIndex + offset) % 12), 4 + offset, 25)).toISOString(),
    listingId: listings[offset].id,
    complaint: complaintTexts[(sellerIndex + offset) % complaintTexts.length],
    attachedImages: 2 + ((sellerIndex + offset) % 4),
    evidenceStatus: (['Verified', 'Pending', 'Insufficient'] as const)[(sellerIndex + offset) % 3],
  }))
}

export const sellers: Seller[] = shops.map(([name, keySignal], index) => {
  const riskScore = [96, 92, 88, 85, 82, 79, 77, 74, 71, 68, 64, 61, 58, 54, 49, 45, 41, 37, 32, 26][index]
  const status = index < 8 ? 'To review' : index < 15 ? 'In progress' : 'Resolved'
  const listings = buildListings(index)
  const reports = buildReports(index, listings)
  return {
    id: `seller-${index + 1}`,
    name,
    shopId: `SG${String(83649102 + index * 7913)}`,
    initials: name.split(' ').map((word) => word[0]).slice(0, 2).join(''),
    recommendation: riskScore >= 75 ? 'Violation confirmed' : riskScore >= 50 ? 'Need more information' : 'No violation',
    riskScore,
    confidence: Math.min(98, 68 + ((index * 7) % 29)),
    keySignal,
    status,
    lastUpdated: new Date(Date.UTC(2026, 10, 20 - (index % 9), 2 + (index % 7), 15)).toISOString(),
    createdAt: new Date(Date.UTC(2023 + (index % 3), (index * 3) % 12, 4 + (index % 20))).toISOString(),
    listingsCount: 18 + ((index * 17) % 184),
    category: listings[0].category,
    fulfillment: index % 3 === 0 ? 'Shopee supported fulfillment' : index % 3 === 1 ? 'Seller managed, domestic' : 'Seller managed, cross border',
    previousInvestigations: index % 5,
    summary: `${reports.length} buyer reports show recurring differences between advertised product details and received items. Visual analysis found the strongest divergence in model geometry, packaging and version identifiers. The recommendation is based on corroborating evidence across ${listings.length} listings.`,
    listings,
    reports,
  } satisfies Seller
})

export const outcomeData = [
  { name: 'Violation confirmed', value: 37, color: '#EE4D2D' },
  { name: 'No violation', value: 24, color: '#2F7D67' },
  { name: 'More information', value: 18, color: '#D99022' },
]

export const weeklyData = [
  { week: '27 Oct', investigations: 42, resolved: 31 },
  { week: '3 Nov', investigations: 49, resolved: 39 },
  { week: '10 Nov', investigations: 46, resolved: 41 },
  { week: '17 Nov', investigations: 57, resolved: 44 },
]
