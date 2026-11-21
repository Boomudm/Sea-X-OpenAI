import { useEffect, type ReactNode } from 'react'
import { X } from 'lucide-react'
import { Button } from './Button'

interface DrawerProps {
  open: boolean
  onClose: () => void
  title: string
  description: string
  children: ReactNode
}

export function Drawer({ open, onClose, title, description, children }: DrawerProps) {
  useEffect(() => {
    if (!open) return
    const listener = (event: KeyboardEvent) => event.key === 'Escape' && onClose()
    document.addEventListener('keydown', listener)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', listener)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-x-0 bottom-0 top-16 z-[200] bg-ink/45 backdrop-blur-sm" role="presentation" onMouseDown={onClose}>
      <aside className="ml-auto flex h-full w-full max-w-2xl flex-col bg-white shadow-float" role="dialog" aria-modal="true" aria-labelledby="drawer-title" onMouseDown={(event) => event.stopPropagation()}>
        <div className="flex items-start justify-between gap-4 border-b border-line p-6">
          <div className="max-w-xl">
            <p className="eyebrow mb-2">Capture evidence</p>
            <h2 id="drawer-title" className="heading-5">{title}</h2>
            <p className="body-6 mt-2 text-muted">{description}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close evidence form"><X className="size-5" /></Button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-6">{children}</div>
      </aside>
    </div>
  )
}
