import { useEffect, type ReactNode } from 'react'
import { X } from 'lucide-react'
import { Button } from './Button'

interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: ReactNode
}

export function Dialog({ open, onClose, title, description, children }: DialogProps) {
  useEffect(() => {
    if (!open) return
    const listener = (event: KeyboardEvent) => event.key === 'Escape' && onClose()
    document.addEventListener('keydown', listener)
    return () => document.removeEventListener('keydown', listener)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-ink/50 p-4 backdrop-blur-sm" role="presentation" onMouseDown={onClose}>
      <div className="w-full max-w-lg rounded-xl border border-line bg-white p-6 shadow-float" role="dialog" aria-modal="true" aria-labelledby="dialog-title" onMouseDown={(event) => event.stopPropagation()}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="dialog-title" className="heading-6">{title}</h2>
            {description && <p className="body-6 mt-2 text-muted">{description}</p>}
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close dialog"><X className="size-5" /></Button>
        </div>
        <div className="mt-6">{children}</div>
      </div>
    </div>
  )
}
