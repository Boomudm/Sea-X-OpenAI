import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { ToastProvider } from './components/ui/Toast'
import { InvestigationProvider, useInvestigations } from './hooks/useInvestigations'
const ReviewQueuePage = lazy(() => import('./pages/ReviewQueuePage').then((module) => ({ default: module.ReviewQueuePage })))
const ResultsPage = lazy(() => import('./pages/ResultsPage').then((module) => ({ default: module.ResultsPage })))
const LegalPage = lazy(() => import('./pages/LegalPage').then((module) => ({ default: module.LegalPage })))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then((module) => ({ default: module.NotFoundPage })))

export default function App() {
  return <BrowserRouter><ToastProvider><InvestigationProvider><AppShell><Suspense fallback={<RouteSkeleton />}><Routes>
    <Route path="/" element={<ReviewQueuePage />} />
    <Route path="/review" element={<ReviewQueuePage />} />
    <Route path="/results" element={<ResultsPage />} />
    <Route path="/investigations" element={<Navigate to="/" replace />} />
    <Route path="/investigations/:sellerId" element={<InvestigationRoute />} />
    <Route path="/investigations/:sellerId/evidence" element={<LegacyWorkspaceRedirect />} />
    <Route path="/investigations/:sellerId/analysis" element={<LegacyWorkspaceRedirect />} />
    <Route path="/investigations/:sellerId/decision" element={<LegacyWorkspaceRedirect />} />
    <Route path="/privacy" element={<LegalPage />} />
    <Route path="/terms" element={<LegalPage />} />
    <Route path="*" element={<NotFoundPage />} />
  </Routes></Suspense></AppShell></InvestigationProvider></ToastProvider></BrowserRouter>
}

function InvestigationRoute() {
  const { sellerId = '' } = useParams()
  const { getSeller } = useInvestigations()
  const listingId = sellerId.startsWith('seller-new-') ? getSeller(sellerId)?.listings[0]?.id : undefined
  if (listingId) return <Navigate to={'/review?' + new URLSearchParams({ source: 'captured', status: 'all', priority: 'unknown', case: listingId })} replace />
  return <Navigate to="/review?source=sample" replace />
}

function LegacyWorkspaceRedirect() {
  const { sellerId = '' } = useParams()
  return <Navigate to={`/investigations/${sellerId}`} replace />
}

function RouteSkeleton() {
  return <div className="page-container" aria-label="Loading page"><div className="h-8 w-72 animate-pulse rounded-lg bg-stone-200" /><div className="mt-3 h-5 w-full max-w-xl animate-pulse rounded bg-stone-100" /><div className="mt-8 grid gap-4 md:grid-cols-3">{Array.from({ length: 3 }).map((_, index) => <div key={index} className="h-32 animate-pulse rounded-xl bg-stone-100" />)}</div><div className="mt-6 h-80 animate-pulse rounded-xl bg-stone-100" /></div>
}
