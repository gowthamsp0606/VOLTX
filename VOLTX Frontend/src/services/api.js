// All API calls go through this service.
// Base URL is built from the IP the user types into the dashboard.

export function buildBase(ip) {
  return `http://${ip}:8000`
}

export async function fetchStatus(ip) {
  const res = await fetch(`${buildBase(ip)}/status`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function fetchHistory(ip) {
  const res = await fetch(`${buildBase(ip)}/history`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}
