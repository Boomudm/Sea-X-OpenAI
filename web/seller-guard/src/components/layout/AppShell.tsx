import { useState, type ReactNode } from 'react'
import { Search, ShoppingBag, UserRound } from 'lucide-react'
import { Link, NavLink, useNavigate, useSearchParams } from 'react-router-dom'

export function AppShell({ children }: { children: ReactNode }) {
  const [globalSearch, setGlobalSearch] = useState('')
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const source = params.get('source')
  const hasSource = source === 'sample' || source === 'captured'
  const sourceSearch = hasSource ? '?' + new URLSearchParams({ source }) : ''
  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault()
    const search = new URLSearchParams({ q: globalSearch.trim(), status: 'all' })
    if (hasSource) search.set('source', source)
    navigate('/review?' + search)
  }
  return (
    <div className="relative min-h-screen overflow-hidden bg-canvas">
      <div aria-hidden="true" className="pointer-events-none fixed -right-24 top-20 z-0 h-72 w-96 rotate-[-18deg] rounded-full bg-[#FFE5D9]/60" />
      <div aria-hidden="true" className="pointer-events-none fixed -left-32 bottom-16 z-0 h-64 w-96 rotate-12 rounded-full bg-[#FFF0E9]/80" />
      <a href="#main-content" className="focus-ring fixed left-4 top-2 z-[100] -translate-y-20 rounded-lg bg-ink px-3 py-2 text-sm font-semibold text-white focus:translate-y-0">Skip to content</a>
      <header className="sticky top-0 z-50 border-b border-line bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1560px] items-center gap-4 px-4 md:px-8">
          <NavLink to={'/' + sourceSearch} className="focus-ring flex shrink-0 items-center gap-2 rounded-lg" aria-label="Seller Guard home">
            <span className="relative flex size-9 items-center justify-center text-brand"><ShoppingBag className="absolute inset-0 size-9 fill-brand stroke-brand" /><span className="relative mt-1 text-xl font-semibold text-white">S</span></span>
            <span className="leading-tight"><strong className="block text-base font-semibold text-ink">Seller Guard</strong><span className="hidden text-sm text-muted sm:block">Trust &amp; Safety</span></span>
          </NavLink>
          <nav className="hidden h-full items-center gap-2 lg:flex" aria-label="Primary navigation">
            <NavLink to={'/' + sourceSearch} end className={({ isActive }) => isActive ? 'review-nav is-current' : 'review-nav'}>Review overview</NavLink>
            <NavLink to={'/review' + sourceSearch} className={({ isActive }) => isActive ? 'review-nav is-current' : 'review-nav'}>Review queue</NavLink>
            <NavLink to={'/results' + sourceSearch} className={({ isActive }) => isActive ? 'review-nav is-current' : 'review-nav'}>Results</NavLink>
          </nav>
          <div className="ml-auto hidden items-center gap-3 md:flex">
            <form onSubmit={submitSearch} className="relative w-52 xl:w-72">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
              <input className="form-control w-full pl-9" value={globalSearch} onChange={(event) => setGlobalSearch(event.target.value)} placeholder="Search listings or ID" aria-label="Global search" />
            </form>
            <div className="flex items-center gap-2 p-1">
              <span className="flex size-8 items-center justify-center rounded-full bg-ink text-white"><UserRound className="size-4" /></span>
              <span className="hidden whitespace-nowrap text-left xl:block"><strong className="block text-sm font-semibold">Local reviewer</strong><span className="block text-sm text-muted">Review workspace</span></span>
            </div>
          </div>
          <span className="ml-auto text-sm font-semibold text-muted md:hidden">Demo workspace</span>
        </div>
      </header>
      <main id="main-content">{children}</main>
      <footer className="border-t border-line bg-white py-6 print:hidden">
        <div className="mx-auto flex max-w-[1480px] flex-col gap-2 px-4 text-sm text-muted md:flex-row md:items-center md:justify-between md:px-8">
          <p>Reviewer decisions and submitted links are stored in this browser.</p>
          <div className="flex gap-4"><Link className="focus-ring rounded hover:text-ink lg:hidden" to={'/results' + sourceSearch}>Results</Link><a className="focus-ring rounded hover:text-ink" href="/privacy">Privacy</a><a className="focus-ring rounded hover:text-ink" href="/terms">Terms</a></div>
        </div>
      </footer>
    </div>
  )
}
