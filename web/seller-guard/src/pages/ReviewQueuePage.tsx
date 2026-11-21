import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useMatch, useSearchParams } from 'react-router-dom'
import { PageHeader } from '../components/layout/PageHeader'
import { AddCaseDrawer } from '../components/investigations/AddCaseDrawer'
import { ReviewCaseModal, type ReviewSubmission } from '../components/investigations/ReviewCaseModal'
import { ReviewOverview } from '../components/investigations/ReviewOverview'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { useToast } from '../components/ui/Toast'
import {
  buildReviewCases, confidenceBands, inConfidenceBand, priorities, signals,
  type ConfidenceBand, type ReviewCase, type ReviewPriority, type ReviewSignal,
} from '../data/reviewCases'
import { useInvestigations } from '../hooks/useInvestigations'

const pageSize = 8
const statuses = {
  ready: 'To review',
  progress: 'In progress',
  resolved: 'Resolved',
  all: 'All statuses',
} as const

function knownKey<T extends Record<string, unknown>>(record: T, value: string | null): keyof T | null {
  return value !== null && Object.prototype.hasOwnProperty.call(record, value) ? value : null
}

function queueLink(priority: ReviewPriority | null, signal?: ReviewSignal, band?: ConfidenceBand) {
  const search = new URLSearchParams()
  if (priority) search.set('priority', priority)
  if (signal && band) {
    search.set('signal', signal)
    search.set('band', band)
  }
  return '/review' + (search.toString() ? '?' + search : '')
}

export function ReviewQueuePage() {
  const { sellers, decisions, submitDecision } = useInvestigations()
  const { toast } = useToast()
  const { pathname } = useLocation()
  const isQueue = useMatch('/review') !== null
  const [params, setParams] = useSearchParams()
  const [addCaseOpen, setAddCaseOpen] = useState(false)
  const [page, setPage] = useState(0)
  const trigger = useRef<HTMLButtonElement | null>(null)
  const nextButton = useRef<HTMLButtonElement>(null)
  const tableTitle = useRef<HTMLHeadingElement>(null)
  const allCases = useMemo(() => buildReviewCases(sellers, decisions), [sellers, decisions])
  const readyCases = useMemo(() => allCases.filter((item) => item.status === 'To review'), [allCases])
  const priority = knownKey(priorities, params.get('priority'))
  const signal = knownKey(signals, params.get('signal'))
  const band = knownKey(confidenceBands, params.get('band'))
  const group = signal && band ? { signal, band } : null
  const query = params.get('q') ?? ''
  const queryText = query.trim().toLowerCase()
  const status = knownKey(statuses, params.get('status')) ?? 'ready'

  const filtered = allCases.filter((item) => {
    if (status !== 'all' && item.status !== statuses[status]) return false
    if (priority && item.priority !== priority) return false
    if (group && !item.findings.some((result) => result.signal === group.signal && inConfidenceBand(result.confidence, group.band))) return false
    return !queryText || [item.title, item.sellerName, item.shopId, item.id].some((value) => value?.toLowerCase().includes(queryText))
  })
  const lastPage = Math.max(0, Math.ceil(filtered.length / pageSize) - 1)
  const currentPage = Math.min(lastPage, page)
  const pageStart = currentPage * pageSize
  const nextCase = filtered.find((item) => item.status === 'To review')
  const caseId = params.get('case')
  const selected = isQueue && caseId ? allCases.find((item) => item.id === caseId) : undefined
  const overviewPriority = priority === 'unknown' ? null : priority
  const overviewLink = overviewPriority ? '/?priority=' + overviewPriority : '/'

  useEffect(() => { setPage(0) }, [pathname, priority, signal, band])
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])

  function updateParams(changes: Record<string, string | null>) {
    setParams((previous) => {
      const next = new URLSearchParams(previous)
      for (const [key, value] of Object.entries(changes)) {
        if (value) next.set(key, value)
        else next.delete(key)
      }
      return next
    }, { replace: true })
  }

  function openCase(item: ReviewCase, origin: HTMLButtonElement | null) {
    trigger.current = origin
    updateParams({ case: item.id })
  }

  function closeCase() {
    updateParams({ case: null })
    requestAnimationFrame(() => {
      if (trigger.current?.isConnected && !trigger.current.disabled) trigger.current.focus()
      else if (nextButton.current && !nextButton.current.disabled) nextButton.current.focus()
      else tableTitle.current?.focus()
      trigger.current = null
    })
  }

  function saveCase(submission: ReviewSubmission) {
    if (!selected) return
    const position = filtered.findIndex((item) => item.id === selected.id)
    const waiting = filtered.filter((item) => item.id !== selected.id && item.status === 'To review')
    const next = filtered.slice(position + 1).find((item) => item.status === 'To review') ?? waiting[0]
    submitDecision(selected.sellerId, submission.outcome, submission.notes, submission.flags, selected.listingId)
    toast(submission.outcome === 'Need more information' ? 'Evidence request recorded.' : 'Reviewer decision saved.')
    if (submission.next && next) {
      const remaining = status === 'all' ? filtered : filtered.filter((item) => item.id !== selected.id)
      setPage(Math.floor(remaining.findIndex((item) => item.id === next.id) / pageSize))
      updateParams({ case: next.id })
    } else {
      closeCase()
    }
  }

  if (!isQueue) return (
    <div className="page-container">
      <PageHeader
        eyebrow="Seller investigations"
        title="Review overview"
        description="Choose a priority, then select a group of SSD cases to review."
        actions={<>
          <Button type="button" variant="outline" onClick={() => setAddCaseOpen(true)}>Add listing links</Button>
          <Link className="review-primary" to={queueLink(overviewPriority)}>Open review queue</Link>
        </>}
      />
      <ReviewOverview
        cases={readyCases}
        priority={overviewPriority}
        onSelect={(id) => updateParams({ priority: id === overviewPriority ? null : id })}
        toQueue={queueLink}
      />
      <p className="caption-5 mt-4 text-muted">Demo scores use sample SSD evidence. Captured links enter the queue as Needs evidence.</p>
      {addCaseOpen && <AddCaseDrawer open onClose={() => setAddCaseOpen(false)} />}
    </div>
  )

  return (
    <div className="page-container">
      <Link to={overviewLink} className="focus-ring mb-3 inline-block rounded text-sm font-semibold text-[#a82d18] hover:underline">Back to overview</Link>
      <PageHeader title="Reviewer workspace" description="Inspect the evidence and record a decision for each case."
        actions={<div className="flex flex-wrap gap-2" aria-label="Selected review group">
          {priority && <Badge tone={priorities[priority].tone}>{priorities[priority].label}</Badge>}
          {group && <><Badge>{signals[group.signal].label}</Badge><Badge>{confidenceBands[group.band].label} confidence</Badge></>}
          {!priority && !group && <Badge>All priorities</Badge>}
        </div>}
      />
      <section className="surface mt-6" aria-labelledby="queue-heading">
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 sm:p-6">
          <h2 ref={tableTitle} tabIndex={-1} id="queue-heading" className="heading-6 flex flex-wrap items-center gap-2 outline-none">
            Cases to review <Badge className="tabular-nums"><span aria-live="polite">{filtered.length}</span></Badge>
          </h2>
          <Button ref={nextButton} type="button" disabled={!nextCase} onClick={() => nextCase && openCase(nextCase, nextButton.current)}>Review next</Button>
        </div>
        <div className="flex flex-wrap items-center gap-3 border-t border-line px-4 py-3 sm:px-6">
          <input type="search" aria-label="Search review cases" className="form-control w-full sm:max-w-xs"
            placeholder="Search listing, seller or case ID" value={query}
            onChange={(event) => { setPage(0); updateParams({ q: event.target.value }) }} />
          <select aria-label="Filter by review status" className="form-control" value={status}
            onChange={(event) => { setPage(0); updateParams({ status: event.target.value === 'ready' ? null : event.target.value }) }}>
            {Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </div>
        <div className="focus-ring overflow-x-auto" tabIndex={0} role="region" aria-label="Cases to review table">
          <table className="w-full min-w-[44rem] border-collapse text-left" aria-labelledby="queue-heading">
            <thead className="border-y border-line bg-[#fff9f5] text-sm text-muted">
              <tr>
                {['Listing', 'Priority', 'Confidence', group ? 'Selected finding' : 'Primary finding', 'Status', 'Review'].map((heading) =>
                  <th scope="col" className="whitespace-nowrap px-4 py-3 first:pl-6 last:pr-6 last:text-right" key={heading}>{heading}</th>)}
              </tr>
            </thead>
            <tbody>
              {filtered.slice(pageStart, pageStart + pageSize).map((item) => {
                const finding = group ? item.findings.find((result) => result.signal === group.signal && inConfidenceBand(result.confidence, group.band)) : item.findings[0]
                const score = finding?.confidence ?? item.confidence
                return (
                  <tr key={item.id} className="cursor-pointer border-b border-line transition-colors hover:bg-peach/60 focus-within:bg-peach/60"
                    onClick={(event) => openCase(item, event.currentTarget.querySelector('button'))}>
                    <td className="py-3 pl-6 pr-4">
                      <strong className="block">{item.title}</strong>
                      <span className="caption-5 block text-muted">{item.sellerName} · {item.id}</span>
                    </td>
                    <td className="px-4 py-3"><Badge tone={priorities[item.priority].tone}>{priorities[item.priority].label}</Badge></td>
                    <td className="px-4 py-3 font-semibold tabular-nums">{score === null ? '—' : `${score}%`}</td>
                    <td className="px-4 py-3">{finding ? signals[finding.signal].label : 'Insufficient evidence'}
                      {!group && item.findings.length > 1 && <span className="caption-5 block text-muted">+{item.findings.length - 1} more</span>}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-muted">{item.status}</td>
                    <td className="py-3 pl-4 pr-6 text-right">
                      <button type="button" aria-haspopup="dialog" aria-label={`Review case ${item.id}`}
                        className="focus-ring whitespace-nowrap rounded px-2 py-2 text-sm font-semibold text-[#a82d18] hover:underline"
                        onClick={(event) => { event.stopPropagation(); openCase(item, event.currentTarget) }}>Open case</button>
                    </td>
                  </tr>
                )
              })}
              {!filtered.length && <tr><td colSpan={6} className="p-6 text-muted">
                No cases match these filters. <Link to="/review" className="focus-ring rounded font-semibold text-[#a82d18] hover:underline">See all open cases</Link>
              </td></tr>}
            </tbody>
          </table>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 text-sm text-muted sm:px-6">
          <span>{filtered.length ? `Showing ${pageStart + 1}–${Math.min(pageStart + pageSize, filtered.length)} of ${filtered.length}` : '0 matching cases'}</span>
          <div className="flex gap-2">
            <Button type="button" size="sm" variant="outline" disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>Previous</Button>
            <Button type="button" size="sm" variant="outline" disabled={currentPage === lastPage} onClick={() => setPage(currentPage + 1)}>Next</Button>
          </div>
        </div>
      </section>
      {selected && <ReviewCaseModal key={selected.id} item={selected} focusedSignal={group?.signal} onClose={closeCase} onSave={saveCase} />}
    </div>
  )
}
