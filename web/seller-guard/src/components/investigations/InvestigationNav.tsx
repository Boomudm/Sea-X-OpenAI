import { NavLink, useParams } from 'react-router-dom'
import { cn } from '../../lib/utils'

const tabs = [
  ['Overview', ''],
  ['Evidence', 'evidence'],
  ['Buyer reports & AI', 'analysis'],
  ['Decision & report', 'decision'],
] as const

export function InvestigationNav() {
  const { sellerId } = useParams()
  return (
    <nav className="no-print flex gap-6 overflow-x-auto rounded-xl border border-line bg-white px-4 shadow-soft" aria-label="Investigation sections">
      {tabs.map(([label, path]) => (
        <NavLink key={path} end={path === ''} to={`/investigations/${sellerId}${path ? `/${path}` : ''}`} className={({ isActive }) => cn('focus-ring relative whitespace-nowrap rounded px-1 py-3 text-base font-medium text-muted transition-colors duration-300 hover:text-ink', isActive && 'text-brand after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-brand')}>{label}</NavLink>
      ))}
    </nav>
  )
}
