import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const formatDate = (value: string) =>
  new Intl.DateTimeFormat('en', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value))

export const formatDateTime = (value: string) =>
  new Intl.DateTimeFormat('en', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value))

export const riskLevel = (score: number) => {
  if (score >= 90) return 'Critical'
  if (score >= 75) return 'High'
  if (score >= 50) return 'Medium'
  return 'Low'
}

export type TreeResult = 'Red' | 'Yellow' | 'Green' | 'Grey'

export const treeResult = (score: number): TreeResult => {
  if (score >= 85) return 'Red'
  if (score >= 60) return 'Yellow'
  if (score < 40) return 'Green'
  return 'Grey'
}

export const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-SG', { style: 'currency', currency: 'SGD' }).format(value)
