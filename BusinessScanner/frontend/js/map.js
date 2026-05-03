// map.js — Leaflet map for business visualization
let map;

export function initMap() {
  map = L.map('map').setView([-33.4489, -70.6693], 10);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);
}

export function addBusinessMarkers(businesses) {
  if (!map) return;
  businesses.forEach(b => {
    if (!b.lat || !b.lng) return;
    const color = b.score >= 80 ? 'green' : b.score >= 70 ? 'yellow' : 'red';
    const marker = L.circleMarker([b.lat, b.lng], {
      radius: 8,
      fillColor: color,
      color: '#333',
      fillOpacity: 0.8
    }).addTo(map);
    marker.bindPopup(`
      <strong>${b.nombre}</strong><br>
      Score: ${b.score || 'N/A'}<br>
      Estado: ${b.estado || 'pendiente'}
    `);
  });
}

// Initialize map on tab show
document.querySelector('[data-tab="mapa"]')?.addEventListener('click', () => {
  setTimeout(() => {
    if (!map) {
      initMap();
      // Load businesses for map
      import('./api.js').then(({ fetchBusinesses }) => {
        fetchBusinesses().then(data => addBusinessMarkers(data));
      });
    }
    map?.invalidateSize();
  }, 100);
});