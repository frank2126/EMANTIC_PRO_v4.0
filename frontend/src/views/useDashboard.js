// useDashboard.js — CORREGIDO
export function useDashboard() {

  function heatColorDPV(val, max) {
    if (!val || val === 0) return '#E5E7EB'
    const r = val / (max || 1)
    if (r >= 0.7) return '#EF4444'
    if (r >= 0.4) return '#F59E0B'
    return '#22C55E'
  }

  function heatColorICO(val, max) {
    if (!val || val === 0) return '#E5E7EB'
    const r = val / (max || 1)
    if (r >= 0.7) return '#F0C419'
    if (r >= 0.4) return '#60b566'
    return '#31b079'
  }

  function heatHeight(val, max, maxPx = 80) {
    if (!max || max <= 0) return 0
    return Math.round((val / max) * maxPx)
  }

  function barPct(val, max) {
    if (!max || max <= 0) return 0
    return Math.round((val / max) * 100)
  }

  function badgeClass(estado) {
    const e = (estado || '').toLowerCase()
    if (e.includes('acept'))   return 'badge-success'
    if (e.includes('rechaz'))  return 'badge-danger'
    if (e.includes('pendien')) return 'badge-warning'
    return 'badge-info'
  }

  function truncar(texto, n = 50) {
    if (!texto) return ''
    const t = String(texto)
    return t.length > n ? t.slice(0, n) + '…' : t
  }

  return { heatColorDPV, heatColorICO, heatHeight, barPct, badgeClass, truncar }
}