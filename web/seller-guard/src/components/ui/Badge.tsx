import type { ReactNode } from 'react'
import { cn } from '../../lib/utils'

type Tone = 'neutral' | 'orange' | 'red' | 'green' | 'yellow' | 'blue'

const tones: Record<Tone, string> = {
  neutral: 'bg-stone-100 text-stone-700',
  orange: 'bg-peach text-[#A82D18]',
  red: 'bg-red-50 text-red-700',
  green: 'bg-emerald-50 text-emerald-700',
  yellow: 'bg-amber-50 text-amber-700',
  blue: 'bg-sky-50 text-sky-700',
}

export function Badge({ children, tone = 'neutral', className }: { children: ReactNode; tone?: Tone; className?: string }) {
  return <span className={cn('inline-flex items-center rounded-full px-2.5 py-1 text-sm font-semibold leading-5', tones[tone], className)}>{children}</span>
}
