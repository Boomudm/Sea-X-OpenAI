import { cn, riskLevel } from '../../lib/utils'

export function RiskScore({ score, compact = false }: { score: number; compact?: boolean }) {
  const level = riskLevel(score)
  return (
    <div className={cn('flex items-center gap-2', !compact && 'min-w-28')}>
      <span className={cn('font-semibold tabular-nums', score >= 90 ? 'text-red-700' : score >= 75 ? 'text-brand' : score >= 50 ? 'text-amber-700' : 'text-emerald-700')}>{score}</span>
      {!compact && <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-stone-100"><div className={cn('h-full rounded-full', level === 'Critical' ? 'bg-red-600' : level === 'High' ? 'bg-brand' : level === 'Medium' ? 'bg-amber-500' : 'bg-emerald-600')} style={{ width: `${score}%` }} /></div>}
    </div>
  )
}
