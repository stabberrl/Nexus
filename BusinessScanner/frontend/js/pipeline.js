// pipeline.js — Pipeline status display
import { checkHealth } from './api.js';

export async function updatePipelineStatus() {
  const container = document.getElementById('pipeline-status');
  if (!container) return;

  try {
    const health = await checkHealth();
    container.innerHTML = `
      <h3>Estado del Sistema</h3>
      <p><strong>Ollama:</strong> ${health.ollama ? '✅ Conectado' : '❌ Desconectado'}</p>
      <p><strong>API:</strong> ${health.status === 'ok' ? '✅ Operativo' : '❌ Error'}</p>
      <p><strong>Próxima ejecución:</strong> <span id="countdown">--:--:--</span></p>
    `;
    // Start countdown timer
    startCountdown();
  } catch (e) {
    container.innerHTML = '<p style="color:#e94560">Error al conectar con el backend</p>';
  }
}

let countdownInterval;
function startCountdown() {
  if (countdownInterval) clearInterval(countdownInterval);
  const target = new Date(Date.now() + 24 * 60 * 60 * 1000); // 24h from now
  countdownInterval = setInterval(() => {
    const diff = target - new Date();
    if (diff <= 0) {
      document.getElementById('countdown').textContent = '00:00:00';
      return;
    }
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    document.getElementById('countdown').textContent =
      `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  }, 1000);
}

updatePipelineStatus();
setInterval(updatePipelineStatus, 60000); // Refresh every minute