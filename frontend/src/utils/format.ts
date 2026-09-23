export function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return '00:00'
  const sec = Math.floor(seconds)
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60

  const pad = (n: number) => n.toString().padStart(2, '0')
  if (h > 0) {
    return `${pad(h)}:${pad(m)}:${pad(s)}`
  }
  return `${pad(m)}:${pad(s)}`
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const h = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${y}-${m}-${day} ${h}:${min}`
  } catch {
    return dateStr
  }
}

export function formatProgressPercent(current: number, total: number): number {
  if (!total || total <= 0) return 0
  const pct = Math.round((current / total) * 100)
  return Math.min(100, Math.max(0, pct))
}

export function getPlatformMeta(siteHost: string | null | undefined): {
  name: string
  color: string
  bgColor: string
  borderColor: string
} {
  const host = (siteHost || '').toLowerCase()

  if (host.includes('bilibili')) {
    return {
      name: 'Bilibili',
      color: 'text-pink-400',
      bgColor: 'bg-pink-500/10',
      borderColor: 'border-pink-500/30'
    }
  }
  if (host.includes('youtube')) {
    return {
      name: 'YouTube',
      color: 'text-red-400',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/30'
    }
  }
  if (host.includes('qq.com') || host.includes('v.qq')) {
    return {
      name: '腾讯视频',
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
      borderColor: 'border-amber-500/30'
    }
  }
  if (host.includes('iqiyi')) {
    return {
      name: '爱奇艺',
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10',
      borderColor: 'border-emerald-500/30'
    }
  }
  if (host.includes('youku')) {
    return {
      name: '优酷',
      color: 'text-sky-400',
      bgColor: 'bg-sky-500/10',
      borderColor: 'border-sky-500/30'
    }
  }
  if (host.includes('douyin')) {
    return {
      name: '抖音',
      color: 'text-cyan-400',
      bgColor: 'bg-cyan-500/10',
      borderColor: 'border-cyan-500/30'
    }
  }

  // Generic fallback
  return {
    name: host || 'Web',
    color: 'text-indigo-400',
    bgColor: 'bg-indigo-500/10',
    borderColor: 'border-indigo-500/30'
  }
}
