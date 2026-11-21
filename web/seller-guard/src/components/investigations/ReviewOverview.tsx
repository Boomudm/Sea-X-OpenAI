import { useEffect, useRef, type MouseEvent } from 'react'
import { Link } from 'react-router-dom'
import {
  bandIds, confidenceBands, inConfidenceBand, priorities, scoredPriorities, signalIds, signals,
  type ConfidenceBand, type ReviewCase, type ReviewPriority, type ReviewSignal,
} from '../../data/reviewCases'
import { cn } from '../../lib/utils'
import { Badge } from '../ui/Badge'

const heatPalettes = {
  all: ['#f3efeb', '#e8e0da', '#d4c7bd', '#b9a79a'],
  red: ['#ffefec', '#fad5cd', '#f3aa9c', '#e67e6d'],
  yellow: ['#fff7e4', '#fce9b9', '#f7d478', '#eebc55'],
  green: ['#eaf7ef', '#d0eadb', '#a8d5ba', '#7bbd99'],
  unknown: ['#f3efeb', '#e8e0da', '#d4c7bd', '#b9a79a'],
}

const selectTones = {
  red: 'border-[#efc9c1] bg-[#fdece8]',
  yellow: 'border-[#eddbae] bg-[#fff3d8]',
  green: 'border-[#c5e2d2] bg-[#e5f5ec]',
}

interface OverviewProps {
  cases: ReviewCase[]
  priority: ReviewPriority | null
  onSelect: (priority: ReviewPriority) => void
  toQueue: (priority: ReviewPriority | null, signal?: ReviewSignal, band?: ConfidenceBand) => string
}

export function ReviewOverview({ cases, priority, onSelect, toQueue }: OverviewProps) {
  const counts = { red: 0, yellow: 0, green: 0, unknown: 0 }
  for (const item of cases) counts[item.priority] += 1
  const matching = priority ? cases.filter((item) => item.priority === priority) : cases
  const palette = heatPalettes[priority ?? 'all']

  return (
    <div className="mt-6 grid gap-4 min-[860px]:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <section className="surface p-4 sm:p-6" aria-labelledby="priority-heading">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 className="heading-6" id="priority-heading">Cases by priority</h2>
            <p className="caption-5 mt-1 text-muted">Select a priority to update the heatmap.</p>
          </div>
          <Badge>{cases.length} to review</Badge>
        </div>
        <div className="my-4 grid grid-cols-[minmax(6.5rem,8rem)_minmax(0,1fr)] items-center gap-3 sm:grid-cols-[minmax(7rem,9.5rem)_minmax(0,1fr)]">
          <PriorityDonut counts={counts} selected={priority} onSelect={onSelect} />
          <div className="space-y-1">
            {scoredPriorities.map((id) => (
              <button
                key={id}
                type="button"
                aria-pressed={priority === id}
                onClick={() => onSelect(id)}
                className={cn('focus-ring flex w-full items-center gap-2 rounded-lg border border-transparent p-2 text-left transition-colors hover:bg-canvas',
                  priority === id && selectTones[id])}
              >
                <span className="size-2.5 shrink-0 rounded-full" style={{ backgroundColor: priorities[id].color }} aria-hidden="true" />
                <span>
                  <span className="block font-semibold">{priorities[id].label}</span>
                  <span className="caption-5 hidden text-muted sm:block">{priorities[id].hint}</span>
                </span>
                <strong className="ml-auto tabular-nums">{counts[id]}</strong>
              </button>
            ))}
          </div>
        </div>
        <Link to={toQueue('unknown')} className="focus-ring flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-semibold text-muted hover:bg-canvas">
          <span className="size-2.5 rounded-full bg-stone-400" aria-hidden="true" />
          Needs evidence <strong className="ml-auto tabular-nums">{counts.unknown}</strong>
        </Link>
      </section>

      <section className="surface p-4 sm:p-6" aria-labelledby="heatmap-heading">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 className="heading-6" id="heatmap-heading">Confidence heatmap</h2>
            <p className="caption-5 mt-1 text-muted">Select a cell to open those cases.</p>
          </div>
          <Badge tone={priority ? priorities[priority].tone : 'neutral'}>{priority ? priorities[priority].label : 'All priorities'}</Badge>
        </div>
        <table className="mt-3 w-full table-fixed border-separate border-spacing-1 text-sm">
          <thead>
            <tr>
              <th className="w-[41%]"><span className="sr-only">Signal</span></th>
              {bandIds.map((id) => (
                <th key={id} scope="col" className="pb-1 font-semibold">
                  {confidenceBands[id].label}
                  <span className="block whitespace-nowrap text-xs font-medium text-muted">{confidenceBands[id].range}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {signalIds.map((signal) => (
              <tr key={signal}>
                <th scope="row" className="pr-1 text-left font-semibold">{signals[signal].label}</th>
                {bandIds.map((band) => {
                  const count = matching.filter((item) =>
                    item.findings.some((finding) => finding.signal === signal && inConfidenceBand(finding.confidence, band)),
                  ).length
                  const cell = 'grid min-h-10 place-items-center rounded-md border border-black/5 font-semibold tabular-nums'
                  return (
                    <td key={band}>
                      {count ? (
                        <Link
                          to={toQueue(priority, signal, band)}
                          aria-label={`Review ${signals[signal].label}, ${confidenceBands[band].label} confidence, ${count} ${count === 1 ? 'case' : 'cases'}`}
                          className={cn(cell, 'focus-ring hover:border-stone-600')}
                          style={{ backgroundColor: palette[count > 4 ? 3 : Math.min(count - 1, 2)] }}
                        >{count}</Link>
                      ) : <span className={cn(cell, 'bg-canvas text-muted')}>0</span>}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="mt-2 flex flex-wrap items-center justify-end gap-1 text-xs text-muted">
          <span>Fewer cases</span>
          {palette.map((color) => <span className="size-3 rounded" style={{ backgroundColor: color }} key={color} aria-hidden="true" />)}
          <span>More cases</span>
        </div>
        <p className="caption-5 mt-2 text-muted">Cases are grouped by the check that set their priority.</p>
      </section>
    </div>
  )
}

type DonutSegment = { id: typeof scoredPriorities[number]; start: number; end: number }
function PriorityDonut({ counts, selected, onSelect }: {
  counts: Record<ReviewPriority, number>
  selected: ReviewPriority | null
  onSelect: (priority: ReviewPriority) => void
}) {
  const canvas = useRef<HTMLCanvasElement>(null)
  const scored = scoredPriorities.reduce((total, id) => total + counts[id], 0)
  const circle = Math.PI * 2
  let start = -Math.PI / 2
  const segments: DonutSegment[] = scoredPriorities.flatMap((id) => {
    if (!counts[id]) return []
    const length = counts[id] / scored * circle
    const gap = counts[id] === scored ? 0 : Math.min(.045, length / 4)
    const arc = { id, start: start + gap, end: start + length - gap }
    start += length
    return [arc]
  })

  useEffect(() => {
    const element = canvas.current
    const context = element?.getContext('2d')
    if (!element || !context) return
    const draw = () => {
      const size = element.clientWidth
      if (!size) return
      const scale = window.devicePixelRatio || 1
      element.width = Math.round(size * scale)
      element.height = Math.round(size * scale)
      context.scale(scale, scale)
      const center = size / 2
      const radius = center - 12
      context.lineWidth = 18
      context.strokeStyle = '#f2ebe7'
      context.beginPath()
      context.arc(center, center, radius, 0, circle)
      context.stroke()
      for (const arc of segments) {
        context.lineWidth = selected === arc.id ? 21 : 18
        context.globalAlpha = selected && selected !== arc.id ? .29 : 1
        context.strokeStyle = priorities[arc.id].color
        context.beginPath()
        context.arc(center, center, radius, arc.start, arc.end)
        context.stroke()
      }
    }
    draw()
    const observer = new ResizeObserver(draw)
    observer.observe(element)
    return () => observer.disconnect()
  }, [circle, segments, selected])

  const selectSegment = (event: MouseEvent<HTMLCanvasElement>) => {
    const rect = event.currentTarget.getBoundingClientRect()
    const center = rect.width / 2
    const x = event.clientX - rect.left - center
    const y = event.clientY - rect.top - center
    const angle = Math.atan2(y, x)
    const ordered = angle < -Math.PI / 2 ? angle + circle : angle
    if (Math.abs(Math.hypot(x, y) - (center - 12)) > 12) return
    const segment = segments.find((arc) => ordered >= arc.start && ordered <= arc.end)
    if (segment) onSelect(segment.id)
  }

  return (
    <div className="relative aspect-square">
      <canvas
        ref={canvas} onClick={selectSegment} className="block size-full cursor-pointer"
        role="img" aria-label="Scored cases by priority. Use the adjacent buttons to filter by keyboard."
      />
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center" aria-hidden="true">
        <strong className="text-3xl font-bold leading-none tabular-nums tracking-tight">{scored}</strong>
        <span className="mt-1 text-xs font-medium text-muted">scored {scored === 1 ? 'case' : 'cases'}</span>
      </div>
    </div>
  )
}
