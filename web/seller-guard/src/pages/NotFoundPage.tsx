import { ShieldQuestion } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui/Button'

export function NotFoundPage() { return <div className="page-container flex min-h-[70vh] items-center justify-center"><div className="max-w-lg text-center"><span className="mx-auto flex size-14 items-center justify-center rounded-xl bg-peach text-brand"><ShieldQuestion className="size-7" /></span><p className="caption-4 mt-6 uppercase tracking-[0.1em] text-brand">404 · Page not found</p><h1 className="heading-2 mt-2">This case route does not exist.</h1><p className="body-3 mt-4 text-muted">The investigation may have moved, or the address may be incomplete. Return to the queue to continue reviewing active cases.</p><Link to="/" className="mt-6 inline-block"><Button>Return to review queue</Button></Link></div></div> }
