import { Fragment, useEffect, useMemo, useRef, useState } from 'react'
import { ChevronDown, ChevronRight, ExternalLink, Store } from 'lucide-react'
import { Link, useLocation, useMatch, useSearchParams } from 'react-router-dom'
import { PageHeader } from '../components/layout/PageHeader'
import { AddCaseDrawer } from '../components/investigations/AddCaseDrawer'
import { ReviewCaseModal, type ReviewSubmission } from '../components/investigations/ReviewCaseModal'
import { ReviewOverview } from '../components/investigations/ReviewOverview'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { useToast } from '../components/ui/Toast'
import {
  buildReviewCases, caseVerdict, confidenceBands, exportableDecisions, inConfidenceBand, priorities, signals,
  type CaseSource, type ConfidenceBand, type ReviewCase, type ReviewPriority, type ReviewSignal,
} from '../data/reviewCases'
import { loadCapturedCases, publicText, type CaptureFeed } from '../data/pipelineCases'
import { useInvestigations } from '../hooks/useInvestigations'

const pageSize = 8
const statuses = {
  ready: 'To review',
  progress: 'In progress',
  resolved: 'Resolved',
  all: 'All statuses',
} as const
const missingShop = 'no-shop'
const shopPriorityLabels = { red: 'RED', yellow: 'YELLOW', unknown: 'GREY', green: 'GREEN' } as const

interface QueueShop {
  name: string
  badge: string | null
  checked: number
  counts: Record<ReviewPriority, number>
}

function shopKey(item: ReviewCase) {
  if (item.source === 'submitted') return 'submitted:' + item.sellerId
  if (item.shopId) return 'shop:' + item.shopId
  return item.sellerName ? 'listing:' + item.listingId : missingShop
}

function collectShops(cases: ReviewCase[]) {
  const shops = new Map<string, QueueShop>()
  for (const item of cases) {
    const key = shopKey(item)
    let shop = shops.get(key)
    if (!shop) {
      const badge = item.pipeline?.shop?.badge
      shop = {
        name: item.sellerName ?? (item.shopId ? 'Shop ' + item.shopId : 'Shop not recorded'),
        badge: badge === 'mall' ? 'Mall' : badge === 'preferred' ? 'Preferred' : null,
        checked: 0,
        counts: { red: 0, yellow: 0, unknown: 0, green: 0 },
      }
      shops.set(key, shop)
    }
    if (key !== missingShop && item.pipeline) {
      shop.checked += 1
      shop.counts[item.priority] += 1
    }
  }
  return shops
}

function sortShops([keyA, a]: [string, QueueShop], [keyB, b]: [string, QueueShop]) {
  return Number(keyA === missingShop) - Number(keyB === missingShop) ||
    a.name.localeCompare(b.name) || keyA.localeCompare(keyB)
}

function shopPriorityLink(source: CaseSource, shop: string, priority: ReviewPriority) {
  return '/review?' + new URLSearchParams({ source, shop, priority, status: 'all', group: 'shop' })
}

function knownKey<T extends Record<string, unknown>>(record: T, value: string | null): keyof T | null {
  return value !== null && Object.prototype.hasOwnProperty.call(record, value) ? value : null
}

function queueLink(source: CaseSource, priority: ReviewPriority | null, signal?: ReviewSignal, band?: ConfidenceBand) {
  const search = new URLSearchParams({ source })
  if (priority) search.set('priority', priority)
  if (signal && band) {
    search.set('signal', signal)
    search.set('band', band)
  }
  return '/review?' + search
}

function activeSource(requested: string | null, feedState: CaptureFeed['state']): CaseSource {
  if (requested === 'sample' || requested === 'captured') return requested
  return feedState === 'missing' || feedState === 'error' ? 'sample' : 'captured'
}

function ReviewSourceControls({ source, feedState, onSelect, onRefresh }: Readonly<{
  source: CaseSource
  feedState: CaptureFeed['state']
  onSelect: (source: CaseSource) => void
  onRefresh: () => void
}>) {
  const captured = source === 'captured'
  const unavailable = feedState === 'error' || (captured && feedState === 'missing')
  return (
    <div className="mt-4 flex flex-wrap items-center gap-3">
      <fieldset className="flex gap-1 rounded-lg border border-line bg-white p-1">
        <legend className="sr-only">Case source</legend>
        {(['captured', 'sample'] as const).map((kind) => (
          <Button key={kind} type="button" size="sm" variant={source === kind ? 'secondary' : 'ghost'}
            aria-pressed={source === kind}
            onClick={() => onSelect(kind)}>
            {kind === 'captured' ? 'Captured data' : 'Sample data'}
          </Button>
        ))}
      </fieldset>
      {!captured && <output className="rounded-lg border border-line bg-peach px-3 py-2 text-sm">
        <strong>Sample data.</strong> These USB flash drive cases are for the demo.
      </output>}
      {captured && feedState === 'loading' && <output className="text-sm text-muted">Loading captured reports…</output>}
      {captured && feedState === 'available' && <output className="text-sm text-muted">Showing options scored by the pipeline.</output>}
      {unavailable && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <output>{feedState === 'error' ? 'Captured reports could not be read.' : 'No exported reports are available yet.'}</output>
          <Button type="button" size="sm" variant="outline" onClick={onRefresh}>Refresh reports</Button>
        </div>
      )}
    </div>
  )
}

export function ReviewQueuePage() {
  const { sellers, decisions, submitDecision } = useInvestigations()
  const { toast } = useToast()
  const { pathname } = useLocation()
  const isQueue = useMatch('/review') !== null
  const [params, setParams] = useSearchParams()
  const [addCaseOpen, setAddCaseOpen] = useState(false)
  const [page, setPage] = useState(0)
  const [collapsedShops, setCollapsedShops] = useState<ReadonlySet<string>>(new Set())
  const [feed, setFeed] = useState<CaptureFeed>({ state: 'loading' })
  const [loadAttempt, setLoadAttempt] = useState(0)
  const trigger = useRef<HTMLButtonElement | null>(null)
  const restoreFocus = useRef(false)
  const nextButton = useRef<HTMLButtonElement>(null)
  const tableTitle = useRef<HTMLHeadingElement>(null)
  const source = activeSource(params.get('source'), feed.state)
  const loading = source === 'captured' && feed.state === 'loading'
  const allCases = useMemo(() => buildReviewCases(
    sellers, decisions, feed.state === 'available' ? feed.cases : [], source,
  ), [sellers, decisions, feed, source])
  const shops = useMemo(() => collectShops(allCases), [allCases])
  const orderedShops = useMemo(() => [...shops].sort(sortShops), [shops])
  const shopOrder = useMemo(() => new Map(orderedShops.map(([key], index) => [key, index])), [orderedShops])
  const readyCases = useMemo(() => allCases.filter((item) => item.status === 'To review'), [allCases])
  const priority = knownKey(priorities, params.get('priority'))
  const signal = knownKey(signals, params.get('signal'))
  const band = knownKey(confidenceBands, params.get('band'))
  const group = signal && band ? { signal, band } : null
  const query = params.get('q') ?? ''
  const queryText = query.trim().toLowerCase()
  const status = knownKey(statuses, params.get('status')) ?? 'ready'
  const shop = params.get('shop') ?? ''
  const groupByShop = params.get('group') === 'shop'
  const sortByShop = params.get('sort') === 'shop'

  const filtered = allCases.filter((item) => {
    if (status !== 'all' && item.status !== statuses[status]) return false
    if (priority && item.priority !== priority) return false
    if (group && !item.findings.some((result) => result.signal === group.signal && inConfidenceBand(result.confidence, group.band))) return false
    if (shop && shopKey(item) !== shop) return false
    return !queryText || [item.title, item.sellerName, item.shopId, item.caseLabel, item.variant]
      .some((value) => value?.toLowerCase().includes(queryText))
  })
  if (groupByShop || sortByShop) {
    filtered.sort((a, b) => (shopOrder.get(shopKey(a)) ?? 0) - (shopOrder.get(shopKey(b)) ?? 0))
  }
  const lastPage = Math.max(0, Math.ceil(filtered.length / pageSize) - 1)
  const currentPage = Math.min(lastPage, page)
  const pageStart = currentPage * pageSize
  const visibleCases = filtered.slice(pageStart, pageStart + pageSize)
  const visibleGroups = new Map<string, ReviewCase[]>()
  if (groupByShop) {
    for (const item of visibleCases) {
      const key = shopKey(item)
      const cases = visibleGroups.get(key)
      if (cases) cases.push(item)
      else visibleGroups.set(key, [item])
    }
  }
  const nextCase = filtered.find((item) => item.status === 'To review')
  const caseId = params.get('case')
  const selected = isQueue && caseId ? allCases.find((item) => item.id === caseId) : undefined
  const overviewPriority = priority === 'unknown' ? null : priority
  const overviewParams = new URLSearchParams({ source })
  if (overviewPriority) overviewParams.set('priority', overviewPriority)
  const overviewLink = '/?' + overviewParams
  const exportedDecisions = source === 'captured' ? exportableDecisions(allCases) : []

  useEffect(() => {
    const controller = new AbortController()
    loadCapturedCases(controller.signal).then((result) => {
      if (!controller.signal.aborted) setFeed(result)
    }).catch(() => {
      if (!controller.signal.aborted) setFeed({ state: 'error' })
    })
    return () => controller.abort()
  }, [loadAttempt])
  useEffect(() => { setPage(0) }, [pathname, source, priority, signal, band])
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  useEffect(() => {
    if (selected || !restoreFocus.current) return
    restoreFocus.current = false
    if (trigger.current?.isConnected && !trigger.current.disabled) trigger.current.focus()
    else if (nextButton.current && !nextButton.current.disabled) nextButton.current.focus()
    else tableTitle.current?.focus()
    trigger.current = null
  }, [selected])

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
    restoreFocus.current = true
    updateParams({ case: null })
  }

  function setShopCollapsed(key: string, collapsed: boolean) {
    setCollapsedShops((previous) => {
      const next = new Set(previous)
      if (collapsed) next.add(key)
      else next.delete(key)
      return next
    })
  }

  function selectShop(key: string) {
    setPage(0)
    setShopCollapsed(key, false)
    updateParams({ shop: key === shop ? null : key })
  }

  function saveCase(submission: ReviewSubmission) {
    if (!selected) return
    const position = filtered.findIndex((item) => item.id === selected.id)
    const waiting = filtered.filter((item) => item.id !== selected.id && item.status === 'To review')
    const next = filtered.slice(position + 1).find((item) => item.status === 'To review') ?? waiting[0]
    submitDecision(selected.sellerId, submission.outcome, submission.notes, undefined, selected.listingId)
    toast(submission.outcome === 'Need more information' ? 'Evidence request recorded.' : 'Reviewer decision saved.')
    if (submission.next && next) {
      const remaining = status === 'all' ? filtered : filtered.filter((item) => item.id !== selected.id)
      setPage(Math.floor(remaining.findIndex((item) => item.id === next.id) / pageSize))
      updateParams({ case: next.id })
    } else {
      closeCase()
    }
  }

  function downloadDecisions() {
    const blob = new Blob([JSON.stringify(exportedDecisions, null, 2) + '\n'], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'reviewer-decisions.json'
    link.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  const sourceControls = (
    <ReviewSourceControls source={source} feedState={feed.state}
      onSelect={(kind) => updateParams({ source: kind, priority: null, signal: null, band: null, case: null, q: null, status: null, shop: null })}
      onRefresh={() => { setFeed({ state: 'loading' }); setLoadAttempt((n) => n + 1) }} />
  )

  if (!isQueue) return (
    <div className="page-container">
      <PageHeader
        eyebrow="Seller investigations"
        title="Review overview"
        description="Choose a priority, then select a group of USB flash drive options to review."
        actions={<>
          <Button type="button" variant="outline" onClick={() => setAddCaseOpen(true)}>Add listing links</Button>
          <Link className="review-primary" to={queueLink(source, overviewPriority)}>Open review queue</Link>
        </>}
      />
      {sourceControls}
      {!loading && <ReviewOverview
        cases={readyCases}
        priority={overviewPriority}
        onSelect={(id) => updateParams({ priority: id === overviewPriority ? null : id })}
        toQueue={(priority, signal, band) => queueLink(source, priority, signal, band)}
      />}
      <p className="caption-5 mt-4 text-muted">Submitted links stay in this browser for evidence collection.</p>
      {addCaseOpen && <AddCaseDrawer open onClose={() => setAddCaseOpen(false)} />}
    </div>
  )

  function renderCase(item: ReviewCase) {
    const finding = group ? item.findings.find((result) => result.signal === group.signal && inConfidenceBand(result.confidence, group.band)) : item.findings[0]
    const score = finding?.confidence ?? item.confidence
    const [primaryReason, ...otherReasons] = item.pipeline?.reasons ?? []
    const fallbackFinding = finding ? signals[finding.signal].label : 'Insufficient evidence'
    const key = shopKey(item)
    const shopName = shops.get(key)?.name ?? 'Shop not recorded'
    return (
      <tr key={item.id} className="cursor-pointer border-b border-line transition-colors hover:bg-peach/60 focus-within:bg-peach/60"
        onClick={(event) => {
          if (event.target instanceof Element && event.target.closest('a')) return
          openCase(item, event.currentTarget.querySelector<HTMLButtonElement>('[aria-haspopup="dialog"]'))
        }}>
        <td className="py-3 pl-6 pr-4">
          <strong className="block">
            {item.title}
            {item.shopee && <a href={item.shopee.url} target="_blank" rel="noopener noreferrer"
              aria-label={`Open ${item.title} on Shopee (opens in a new tab)`}
              className="focus-ring ml-1 inline-grid min-h-11 min-w-11 place-items-center rounded-md align-middle text-[#a82d18] hover:bg-peach sm:min-h-8 sm:min-w-8">
              <ExternalLink className="size-4" aria-hidden="true" />
            </a>}
          </strong>
          <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
            <button type="button" aria-label={`Filter by shop: ${shopName}`} aria-pressed={shop === key}
              className="focus-ring group inline-flex min-h-11 items-center rounded-full text-left sm:min-h-0"
              onClick={(event) => { event.stopPropagation(); selectShop(key) }}>
              <Badge tone={shop === key ? 'orange' : 'neutral'} className="gap-1.5 py-0.5 text-xs group-hover:bg-peach">
                <Store aria-hidden="true" className="size-3.5 shrink-0" />{shopName}
              </Badge>
            </button>
            <span className="caption-5 text-muted">{[item.variant, item.caseLabel].filter(Boolean).join(' · ')}</span>
          </div>
        </td>
        <td className="px-4 py-3"><Badge tone={priorities[item.priority].tone}>{priorities[item.priority].label}</Badge></td>
        <td className="px-4 py-3 font-semibold tabular-nums">{score === null ? '—' : `${score}%`}</td>
        <td className="px-4 py-3">{primaryReason ? publicText(primaryReason) : fallbackFinding}
          {otherReasons.length > 0 && <span className="caption-5 block text-muted">+{otherReasons.length} more</span>}
        </td>
        <td className="whitespace-nowrap px-4 py-3 text-sm text-muted">
          {item.status}<span className="caption-5 block">{caseVerdict(item.decision)}</span>
        </td>
        <td className="py-3 pl-4 pr-6 text-right">
          <button type="button" aria-haspopup="dialog" aria-label={`Review ${item.title}${item.variant ? ' · ' + item.variant : ''} · ${item.caseLabel}`}
            className="focus-ring whitespace-nowrap rounded px-2 py-2 text-sm font-semibold text-[#a82d18] hover:underline"
            onClick={(event) => { event.stopPropagation(); openCase(item, event.currentTarget) }}>Open case</button>
        </td>
      </tr>
    )
  }

  return (
    <div className={groupByShop ? 'page-container review-queue-grouped' : 'page-container'}>
      <Link to={overviewLink} className="focus-ring mb-3 inline-block rounded text-sm font-semibold text-[#a82d18] hover:underline">Back to overview</Link>
      <PageHeader title="Reviewer workspace" description="Inspect the evidence and record a decision for each case."
        actions={<div className="flex flex-wrap gap-2" aria-label="Selected review group">
          {priority && <Badge tone={priorities[priority].tone}>{priorities[priority].label}</Badge>}
          {group && <><Badge>{signals[group.signal].label}</Badge><Badge>{confidenceBands[group.band].label} confidence</Badge></>}
          {!priority && !group && <Badge>All priorities</Badge>}
        </div>}
      />
      {sourceControls}
      {!loading && <section className="review-queue-panel surface mt-6" aria-labelledby="queue-heading">
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 sm:p-6">
          <h2 ref={tableTitle} tabIndex={-1} id="queue-heading" className="heading-6 flex flex-wrap items-center gap-2 outline-none">
            {groupByShop ? 'Review priority by shop' : 'Cases to review'} <Badge className="tabular-nums"><span aria-live="polite">{filtered.length}</span></Badge>
          </h2>
          <div className="flex flex-wrap gap-2">
            {source === 'captured' && <Button type="button" variant="outline" disabled={!exportedDecisions.length}
              title={exportedDecisions.length ? undefined : 'Review a pipeline option to export its decision'}
              onClick={downloadDecisions}>Export decisions</Button>}
            <Button ref={nextButton} type="button" disabled={!nextCase} onClick={() => nextCase && openCase(nextCase, nextButton.current)}>Review next</Button>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 border-t border-line px-4 py-3 sm:px-6">
          <input type="search" aria-label="Search review cases" className="form-control w-full sm:max-w-xs"
            placeholder="Search listing, shop or case ID" value={query}
            onChange={(event) => { setPage(0); updateParams({ q: event.target.value }) }} />
          <select aria-label="Filter by review status" className="form-control" value={status}
            onChange={(event) => { setPage(0); updateParams({ status: event.target.value === 'ready' ? null : event.target.value }) }}>
            {Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
          <select aria-label="Filter by shop" className="form-control max-w-full sm:max-w-56" value={shop}
            onChange={(event) => selectShop(event.target.value)}>
            <option value="">All shops</option>
            {orderedShops.map(([key, entry]) => <option key={key} value={key}>{entry.name}</option>)}
          </select>
          {!groupByShop && <select aria-label="Sort cases" className="form-control max-w-full" value={sortByShop ? 'shop' : 'priority'}
            onChange={(event) => { setPage(0); updateParams({ sort: event.target.value === 'shop' ? 'shop' : null }) }}>
            <option value="priority">Review priority</option>
            <option value="shop">Shop name A–Z</option>
          </select>}
          <Button type="button" variant={groupByShop ? 'secondary' : 'outline'} aria-pressed={groupByShop}
            onClick={() => { setPage(0); updateParams({ group: groupByShop ? null : 'shop' }) }}>Group by shop</Button>
        </div>
        {groupByShop && filtered.length > 0 && shops.size > Number(shops.has(missingShop)) && <p className="border-t border-line px-4 py-2 text-sm text-muted sm:px-6">
          Shops are listed by name. Counts cover all checked options in this data source.
        </p>}
        <div className="review-queue-scroll focus-ring overflow-x-auto" tabIndex={0} role="region" aria-label="Cases to review table">
          <table className="w-full min-w-[44rem] border-collapse text-left" aria-labelledby="queue-heading">
            <thead className="border-y border-line bg-[#fff9f5] text-sm text-muted">
              <tr>
                {['Listing', 'Priority', 'Confidence', group ? 'Selected finding' : 'Primary finding', 'Status', 'Review'].map((heading) =>
                  <th scope="col" className="whitespace-nowrap px-4 py-3 first:pl-6 last:pr-6 last:text-right" key={heading}>{heading}</th>)}
              </tr>
            </thead>
            {!groupByShop && visibleCases.length > 0 && <tbody>{visibleCases.map(renderCase)}</tbody>}
            {groupByShop && orderedShops.map(([key, entry], index) => {
              const cases = visibleGroups.get(key)
              if (!cases) return null
              const expanded = !collapsedShops.has(key)
              const contentId = 'shop-options-' + index
              const Chevron = expanded ? ChevronDown : ChevronRight
              return <Fragment key={key}>
                <tbody>
                  <tr className="border-y border-line bg-canvas">
                    <td colSpan={6} className="px-4 py-1 sm:px-6">
                      <div className="flex min-w-0 flex-wrap items-center gap-x-3">
                        <button type="button" className="focus-ring inline-flex min-h-11 min-w-0 max-w-full items-center gap-2 rounded text-left font-semibold hover:underline"
                          aria-expanded={expanded} aria-controls={contentId} id={contentId + '-heading'}
                          onClick={() => setShopCollapsed(key, expanded)}>
                          <Chevron aria-hidden="true" className="size-4 shrink-0 text-muted" />
                          <span className="min-w-0 [overflow-wrap:anywhere]">{entry.name}</span>
                          {entry.badge && <Badge className="shrink-0 py-0.5 text-xs">{entry.badge}</Badge>}
                        </button>
                        {entry.checked > 0 && <div className="flex flex-wrap gap-x-2" role="group" aria-label="Checked options by priority">
                          {(Object.keys(shopPriorityLabels) as ReviewPriority[]).filter((colour) => entry.counts[colour] > 0).map((colour) =>
                            <Link key={colour} to={shopPriorityLink(source, key, colour)}
                              className="focus-ring inline-flex min-h-11 items-center rounded-full hover:underline"
                              aria-label={`View ${entry.counts[colour]} ${shopPriorityLabels[colour]} of ${entry.checked} checked options for ${entry.name}`}
                              onClick={() => { setPage(0); setShopCollapsed(key, false) }}>
                              <Badge tone={priorities[colour].tone} className="py-0.5 text-xs tabular-nums">
                                {entry.counts[colour]} {shopPriorityLabels[colour]} of {entry.checked} checked
                              </Badge>
                            </Link>)}
                        </div>}
                      </div>
                    </td>
                  </tr>
                </tbody>
                <tbody id={contentId} aria-labelledby={contentId + '-heading'} hidden={!expanded}>{cases.map(renderCase)}</tbody>
              </Fragment>
            })}
            {!filtered.length && <tbody><tr><td colSpan={6} className="p-6 text-muted">
              {query || priority || group || shop || status !== 'ready' ? <>
                No cases match these filters. <Link to={queueLink(source, null)} className="focus-ring rounded font-semibold text-[#a82d18] hover:underline">See all open cases</Link>
              </> : 'There are no open cases in this view.'}
            </td></tr></tbody>}
          </table>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 text-sm text-muted sm:px-6">
          <span>{filtered.length ? `Showing ${pageStart + 1}–${Math.min(pageStart + pageSize, filtered.length)} of ${filtered.length}` : '0 matching cases'}</span>
          <div className="flex gap-2">
            <Button type="button" size="sm" variant="outline" disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>Previous</Button>
            <Button type="button" size="sm" variant="outline" disabled={currentPage === lastPage} onClick={() => setPage(currentPage + 1)}>Next</Button>
          </div>
        </div>
      </section>}
      {selected && !loading && <ReviewCaseModal key={selected.id} item={selected} onClose={closeCase} onSave={saveCase} />}
    </div>
  )
}
