import { useEffect, useState } from 'react'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'

const reportTitle = '# Buyer-evidence evaluation'
const protocolUrl = 'https://github.com/Boomudm/Sea-X-OpenAI/blob/prep/research/eval/protocol.md'

type ReportState =
  | { status: 'loading' | 'missing' | 'error' }
  | { status: 'ready', body: string }

type Block =
  | { type: 'heading', text: string }
  | { type: 'paragraph', text: string }
  | { type: 'table', headings: string[], rows: string[][] }

function tableCells(line: string) {
  return line.slice(1, -1).split(/(?<!\\)\|/).map((cell) => cell.trim().replace(/\\\|/g, '|'))
}

function parseReport(body: string): Block[] {
  const lines = body.trim().split(/\r?\n/).slice(1).map((line) => line.trim())
  const blocks: Block[] = []
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index]
    if (!line) continue
    if (line.startsWith('## ')) {
      blocks.push({ type: 'heading', text: line.slice(3) })
    } else if (line.startsWith('|') && /^\|[\s:|\-]+\|$/.test(lines[index + 1] ?? '')) {
      const headings = tableCells(line)
      const rows: string[][] = []
      index += 1
      while (lines[index + 1]?.startsWith('|')) {
        index += 1
        rows.push(tableCells(lines[index]))
      }
      blocks.push({ type: 'table', headings, rows })
    } else {
      blocks.push({ type: 'paragraph', text: line })
    }
  }
  return blocks
}

function ReportText({ text }: { text: string }) {
  return text.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/).map((piece, index) => {
    if (piece.startsWith('**') && piece.endsWith('**')) {
      return <strong key={index} className="font-semibold text-ink">{piece.slice(2, -2)}</strong>
    }
    const link = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(piece)
    if (link?.[2] === 'protocol.md') {
      return <a key={index} className="focus-ring font-semibold text-[#a82d18] underline"
        href={protocolUrl}>{link[1]}</a>
    }
    return link?.[1] ?? piece
  })
}

function EvaluationReport({ body }: { body: string }) {
  return (
    <article className="surface mt-6 space-y-4 p-4 sm:p-6" aria-label="Buyer evidence evaluation">
      {parseReport(body).map((block, index) => {
        if (block.type === 'heading') return <h2 key={index} className="heading-6 pt-2">{block.text}</h2>
        if (block.type === 'paragraph') {
          return <p key={index} className="body-3 max-w-prose text-muted"><ReportText text={block.text} /></p>
        }
        return (
          <div key={index} className="focus-ring overflow-x-auto rounded-lg border border-line"
            tabIndex={0} role="region" aria-label={block.headings[0] + ' results'}>
            <table className="w-full border-collapse text-left text-sm tabular-nums">
              <thead className="border-b border-line bg-[#fff9f5] text-muted">
                <tr>{block.headings.map((heading, column) => <th key={column} scope="col" className="px-3 py-2">{heading}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-line">
                {block.rows.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    <th scope="row" className="break-words px-3 py-2 font-semibold">{row[0]}</th>
                    {row.slice(1).map((value, column) => <td key={column} className="break-words px-3 py-2">{value}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
            {block.rows.length === 0 && <p className="caption-5 px-3 py-2 text-muted">No matching results.</p>}
          </div>
        )
      })}
    </article>
  )
}

async function loadReport(signal: AbortSignal): Promise<ReportState> {
  const response = await fetch('/data/results.md', { signal, cache: 'no-cache' })
  if (response.status === 404) return { status: 'missing' }
  if (!response.ok) return { status: 'error' }
  if (response.headers.get('content-type')?.includes('text/html')) return { status: 'missing' }
  const body = (await response.text()).trim()
  if (!body) return { status: 'missing' }
  if (body.split(/\r?\n/, 1)[0] !== reportTitle) return { status: 'error' }
  return { status: 'ready', body }
}

export function ResultsPage() {
  const [report, setReport] = useState<ReportState>({ status: 'loading' })
  const [reload, setReload] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    loadReport(controller.signal)
      .then((result) => { if (!controller.signal.aborted) setReport(result) })
      .catch(() => { if (!controller.signal.aborted) setReport({ status: 'error' }) })
    return () => controller.abort()
  }, [reload])

  return (
    <div className="page-container">
      <PageHeader title="Evaluation results"
        description="See how the pipeline and baselines compare with the frozen buyer evidence labels."
        actions={<Button variant="outline" loading={report.status === 'loading'} type="button" onClick={() => {
          setReport({ status: 'loading' })
          setReload((count) => count + 1)
        }}>Reload results</Button>} />
      {report.status === 'ready'
        ? <EvaluationReport body={report.body} />
        : <div className="surface mt-6 p-4 sm:p-6" role="status">
          <p className="body-3 text-muted">
            {report.status === 'loading' && 'Loading the evaluation report.'}
            {report.status === 'missing' && 'No evaluation report is available. Run the scorer and export its report to see results here.'}
            {report.status === 'error' && 'The evaluation report could not be loaded. Reload results to try again.'}
          </p>
        </div>}
    </div>
  )
}
