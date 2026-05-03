// dashboard.js — Main dashboard logic
import { fetchStats, fetchBusinesses, runCycleNow, checkHealth } from './api.js';

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
  });
});

// Load pipeline stats
async function loadStats() {
  try {
    const stats = await fetchStats();
    const container = document.getElementById('pipeline-stats');
    container.innerHTML = `
      <div class="stat-card">
        <h3>Escaneados</h3>
        <div class="value">${stats.total_businesses || 0}</div>
      </div>
      <div class="stat-card">
        <h3>Analizados</h3>
        <div class="value">${stats.total_analyses || 0}</div>
      </div>
      <div class="stat-card">
        <h3>Contactados</h3>
        <div class="value">${stats.total_outreach || 0}</div>
      </div>
      <div class="stat-card">
        <h3>Entregados</h3>
        <div class="value">${stats.total_sites || 0}</div>
      </div>
    `;
  } catch (e) {
    console.error('Failed to load stats:', e);
  }
}

// Load businesses table
async function loadBusinesses() {
  try {
    const data = await fetchBusinesses();
    const tbody = document.getElementById('businesses-tbody');
    tbody.innerHTML = data.map(b => `
      <tr>
        <td>${b.nombre || 'N/A'}</td>
        <td>${b.zona || 'N/A'}</td>
        <td>${b.score || '-'}</td>
        <td>${b.estado || 'pendiente'}</td>
        <td>${b.email || '-'}</td>
      </tr>
    `).join('');
  } catch (e) {
    console.error('Failed to load businesses:', e);
  }
}

// Run cycle now button
document.getElementById('btn-run-now')?.addEventListener('click', async () => {
  const btn = document.getElementById('btn-run-now');
  btn.disabled = true;
  btn.textContent = 'Ejecutando...';
  try {
    await runCycleNow();
    alert('Ciclo iniciado');
  } catch (e) {
    alert('Error: ' + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Ejecutar ahora';
  }
});

// Initialize
loadStats();
loadBusinesses();
setInterval(loadStats, 30000); // Refresh every 30s