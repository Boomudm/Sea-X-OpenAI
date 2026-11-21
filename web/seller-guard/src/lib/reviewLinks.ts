export function externalUrl(value?: string): URL | null {
  if (typeof value !== 'string' || !value) return null
  try {
    const url = new URL(value)
    return (url.protocol === 'https:' || url.protocol === 'http:') && !url.username && !url.password
      ? url : null
  } catch {
    return null
  }
}

export function shopeeListing(value?: string) {
  const url = externalUrl(value)
  if (!url || (url.hostname !== 'shopee.co.th' && !url.hostname.endsWith('.shopee.co.th'))) return undefined
  const shopId = /^\/product\/(\d+)\/\d+\/?$/.exec(url.pathname)?.[1]
    ?? /-i\.(\d+)\.\d+\/?$/.exec(url.pathname)?.[1]
  return {
    url: url.href,
    shop: shopId ? { id: shopId, url: `https://shopee.co.th/shop/${shopId}` } : undefined,
  }
}

export function evidenceImageUrl(value: string) {
  // Exported originals live under the same site's data/images directory.
  if (value.startsWith('/data/images/')) {
    const url = new URL(value, window.location.origin)
    return url.pathname.startsWith('/data/images/') && /\.(?:jpe?g|png|webp|gif|bmp)$/i.test(url.pathname)
      ? url.pathname : undefined
  }
  const url = externalUrl(value)
  return url && !url.hostname.endsWith('.invalid') ? url.href : undefined
}
