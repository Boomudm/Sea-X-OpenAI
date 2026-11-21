import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { LoaderCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: 'sm' | 'md' | 'icon'
  loading?: boolean
}

const styles: Record<Variant, string> = {
  primary: 'bg-brand text-white hover:bg-[#D94225] shadow-sm',
  secondary: 'bg-peach text-[#A82D18] hover:bg-[#FFE8DC]',
  outline: 'border border-line bg-white text-ink hover:border-stone-300 hover:bg-canvas',
  ghost: 'text-muted hover:bg-peach hover:text-ink',
  danger: 'bg-[#B42318] text-white hover:bg-[#912018]',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = 'primary', size = 'md', loading, children, disabled, ...props }, ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        'focus-ring inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition duration-300 ease-weighted active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50',
        styles[variant],
        size === 'sm' && 'h-10 px-3 text-sm',
        size === 'md' && 'h-11 px-3 text-base',
        size === 'icon' && 'size-11 p-0',
        className,
      )}
      {...props}
    >
      {loading && <LoaderCircle className="size-4 animate-spin" aria-hidden="true" />}
      {children}
    </button>
  )
})
