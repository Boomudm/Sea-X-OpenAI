import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ArrowDownToLine, TrendingUp } from 'lucide-react'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { outcomeData, weeklyData } from '../data/mockData'
import { useInvestigations } from '../hooks/useInvestigations'
import { useToast } from '../components/ui/Toast'

export function ReportsPage() {
  const { sellers, decisions } = useInvestigations()
  const { toast } = useToast()
  const confirmed = decisions.filter((decision) => decision.type === 'Violation confirmed').length
  const download = () => {
    const rows = ['Seller,Shop ID,Risk score,Status', ...sellers.map((seller) => `"${seller.name}",${seller.shopId},${seller.riskScore},${seller.status}`)]
    const blob = new Blob([rows.join('\n')], { type: 'text/csv' }); const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'investigation-report.csv'; anchor.click(); URL.revokeObjectURL(url); toast('Investigation CSV downloaded.')
  }
  return (
    <div className="page-container">
      <PageHeader eyebrow="Operational insight" title="Investigation reports" description="Monitor case volume, outcomes and review throughput without losing the context behind each decision." actions={<Button variant="outline" onClick={download}><ArrowDownToLine className="size-4" />Export CSV</Button>} />
      <section className="mt-8 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{[
        ['Total investigations', sellers.length, '+8.4% from prior period'], ['Flagged investigations', sellers.filter((seller) => seller.riskScore >= 75).length, 'Risk score 75 or higher'], ['Confirmed violations', confirmed, 'Based on reviewer decisions'], ['Resolved cases', sellers.filter((seller) => seller.status === 'Resolved').length, 'Closed investigations'],
      ].map(([label, value, detail]) => <div key={String(label)} className="surface p-5"><p className="title-4 text-muted">{label}</p><p className="mt-3 text-3xl font-semibold tabular-nums">{value}</p><p className="caption-5 mt-2 flex items-center gap-1 text-muted"><TrendingUp className="size-3.5 text-emerald-600" />{detail}</p></div>)}</section>
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_0.8fr]">
        <section className="surface p-6"><div><p className="caption-4 text-brand">Throughput</p><h2 className="heading-6 mt-1">Weekly investigations and resolutions</h2></div><div className="mt-6 h-80"><ResponsiveContainer width="100%" height="100%"><BarChart data={weeklyData} barGap={4}><CartesianGrid stroke="#EAE3DF" vertical={false} /><XAxis dataKey="week" tickLine={false} axisLine={false} tick={{ fill: '#78716C', fontSize: 14 }} /><YAxis tickLine={false} axisLine={false} tick={{ fill: '#78716C', fontSize: 14 }} /><Tooltip cursor={{ fill: '#FFF4EE' }} contentStyle={{ border: '1px solid #EAE3DF', borderRadius: 8, boxShadow: '0 10px 30px rgba(71,42,32,.08)' }} /><Bar dataKey="investigations" fill="#EE4D2D" radius={[6, 6, 0, 0]} /><Bar dataKey="resolved" fill="#2F7D67" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer></div><div className="mt-4 flex gap-5 text-sm text-muted"><span className="flex items-center gap-2"><i className="size-2 rounded-full bg-brand" />Investigations</span><span className="flex items-center gap-2"><i className="size-2 rounded-full bg-[#2F7D67]" />Resolved</span></div></section>
        <section className="surface p-6"><div><p className="caption-4 text-brand">Outcomes</p><h2 className="heading-6 mt-1">Investigation outcomes</h2></div><div className="mt-3 h-60"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={outcomeData} dataKey="value" nameKey="name" innerRadius={62} outerRadius={90} paddingAngle={3}>{outcomeData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}</Pie><Tooltip contentStyle={{ border: '1px solid #EAE3DF', borderRadius: 8 }} /></PieChart></ResponsiveContainer></div><div className="space-y-2">{outcomeData.map((entry) => <div key={entry.name} className="flex items-center justify-between text-base"><span className="flex items-center gap-2 text-muted"><i className="size-2.5 rounded-full" style={{ background: entry.color }} />{entry.name}</span><strong>{entry.value}%</strong></div>)}</div></section>
      </div>
    </div>
  )
}
