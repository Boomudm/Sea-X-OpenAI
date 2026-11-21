import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import { sellers as seedSellers } from '../data/mockData'
import type { Decision, DecisionType, NewCaseInput, Seller } from '../types'

interface InvestigationContextValue {
  sellers: Seller[]
  decisions: Decision[]
  addCase: (input: NewCaseInput) => Seller
  submitDecision: (sellerId: string, type: DecisionType, notes: string, flagDecisions?: Decision['flagDecisions'], listingId?: string) => Decision
  requestInformation: (sellerId: string, notes?: string) => Decision
  getSeller: (sellerId: string) => Seller | undefined
}

const InvestigationContext = createContext<InvestigationContextValue | null>(null)
const STORAGE_KEY = 'shopee-ts-decisions-v1'
const CASES_STORAGE_KEY = 'shopee-ts-submitted-cases-v1'

function readDecisions(): Decision[] {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return value ? JSON.parse(value) : []
  } catch {
    return []
  }
}

function readCases(): Seller[] {
  try {
    const value = localStorage.getItem(CASES_STORAGE_KEY)
    return value ? JSON.parse(value) : []
  } catch {
    return []
  }
}

export function InvestigationProvider({ children }: { children: ReactNode }) {
  const [decisions, setDecisions] = useState<Decision[]>(readDecisions)
  const [submittedCases, setSubmittedCases] = useState<Seller[]>(readCases)

  const sellers = useMemo(() => [...submittedCases, ...seedSellers].map((seller) => {
    const sellerDecisions = decisions.filter((item) => item.sellerId === seller.id)
    if (!sellerDecisions.length) return seller
    const legacyDecision = sellerDecisions.find((item) => !item.listingId)
    const results = seller.listings.map((listing) =>
      sellerDecisions.find((item) => item.listingId === listing.id) ?? legacyDecision)
    const resolved = results.length > 0 && results.every((item) => item && item.type !== 'Need more information')
    return { ...seller, status: resolved ? 'Resolved' as const : 'In progress' as const, lastUpdated: sellerDecisions[0].timestamp }
  }), [decisions, submittedCases])

  const addCase = useCallback((input: NewCaseInput) => {
    const now = new Date().toISOString()
    const stamp = Date.now()
    const urls = [...new Set(input.listingUrls)].slice(0, 10)
    const listings = urls.map((listingUrl, index) => ({
      id: `LST-NEW-${stamp}-${index + 1}`,
      title: 'SSD listing ' + (index + 1),
      sku: `CAP-${String(stamp).slice(-6)}-${index + 1}`,
      category: 'Storage',
      listingUrl,
      referenceUrl: input.referenceUrls[index] ?? (input.referenceUrls.length === 1 ? input.referenceUrls[0] : undefined),
      price: index === 0 ? input.currentPrice ?? 0 : 0,
      previousPrice: index === 0 ? input.previousPrice : undefined,
      advertisedImage: '',
      receivedImage: '',
      discrepancy: 'Variant and evidence still need verification.',
      findings: [],
    }))
    const seller: Seller = {
      id: `seller-new-${stamp}`,
      name: input.sellerName.trim(),
      shopId: `CAP${String(stamp).slice(-8)}`,
      initials: input.sellerName.trim().split(/\s+/).map((word) => word[0]).slice(0, 2).join('').toUpperCase(),
      recommendation: 'Need more information',
      riskScore: 45,
      confidence: 0,
      keySignal: 'Needs evidence',
      status: 'To review',
      lastUpdated: now,
      createdAt: now,
      listingsCount: listings.length,
      category: 'Storage',
      fulfillment: 'Unknown',
      previousInvestigations: 0,
      summary: 'Listing sources are saved and ready for evidence collection.',
      listings,
      submittedEvidence: { photoCount: input.buyerPhotoCount, currentPrice: input.currentPrice },
      reports: listings[0] && input.complaint.trim() ? [{
        id: `RPT-NEW-${stamp}`,
        buyerName: 'Submitted evidence',
        reportedAt: now,
        listingId: listings[0].id,
        complaint: input.complaint.trim(),
        attachedImages: input.buyerPhotoCount,
        evidenceStatus: 'Pending',
      }] : [],
    }
    setSubmittedCases((current) => {
      const next = [seller, ...current]
      localStorage.setItem(CASES_STORAGE_KEY, JSON.stringify(next))
      return next
    })
    return seller
  }, [])

  const submitDecision = useCallback((sellerId: string, type: DecisionType, notes: string, flagDecisions?: Decision['flagDecisions'], listingId?: string) => {
    const decision: Decision = {
      sellerId, type, notes: notes.trim(), reviewer: 'Alex Morgan', timestamp: new Date().toISOString(), flagDecisions, listingId,
    }
    setDecisions((current) => {
      const next = [decision, ...current.filter((item) => item.sellerId !== sellerId || item.listingId !== listingId)]
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      return next
    })
    return decision
  }, [])

  const requestInformation = useCallback((sellerId: string, notes = 'Additional seller documentation and product provenance requested.') =>
    submitDecision(sellerId, 'Need more information', notes), [submitDecision])

  const getSeller = useCallback((sellerId: string) => sellers.find((seller) => seller.id === sellerId), [sellers])

  return <InvestigationContext.Provider value={{ sellers, decisions, addCase, submitDecision, requestInformation, getSeller }}>{children}</InvestigationContext.Provider>
}

export function useInvestigations() {
  const context = useContext(InvestigationContext)
  if (!context) throw new Error('useInvestigations must be used within InvestigationProvider')
  return context
}
