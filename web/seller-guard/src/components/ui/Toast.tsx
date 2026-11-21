import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import { CheckCircle2, X } from 'lucide-react'

interface ToastItem { id: number; message: string }
interface ToastContextValue { toast: (message: string) => void }
const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])
  const toast = useCallback((message: string) => {
    const id = Date.now()
    setItems((current) => [...current, { id, message }])
    window.setTimeout(() => setItems((current) => current.filter((item) => item.id !== id)), 3600)
  }, [])
  const value = useMemo(() => ({ toast }), [toast])
  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2" aria-live="polite">
        {items.map((item) => (
          <div key={item.id} className="flex items-center gap-3 rounded-xl border border-line bg-white p-4 shadow-float">
            <CheckCircle2 className="size-5 shrink-0 text-emerald-600" aria-hidden="true" />
            <p className="body-6 flex-1 text-ink">{item.message}</p>
            <button className="focus-ring rounded p-1 text-muted hover:bg-stone-100" onClick={() => setItems((current) => current.filter((toastItem) => toastItem.id !== item.id))} aria-label="Dismiss notification"><X className="size-4" /></button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used within ToastProvider')
  return context
}
