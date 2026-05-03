// api.js — API client for AgenteWeb backend
const API_BASE = 'http://localhost:8000/api';

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/dashboard/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchBusinesses() {
  const res = await fetch(`${API_BASE}/dashboard/businesses`);
  if (!res.ok) throw new Error('Failed to fetch businesses');
  return res.json();
}

export async function runCycleNow() {
  const res = await fetch(`${API_BASE}/dashboard/run-now`, { method: 'POST' });
  return res.json();
}

export async function checkHealth() {
  const res = await fetch(`${API_BASE.replace('/api','')}/health`);
  return res.json();
}