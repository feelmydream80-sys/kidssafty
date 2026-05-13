// js/zoneManager.js - 마커 및 패널 관리
import { childSafetyZones, APP_CONFIG } from './config.js';
import { getDistance } from './userLocation.js';

let connectingLines = [];

function cleanLocation(location) {
    if (!location) return '';
    return location.replace(/^서울특별시\s*/, '').replace(/^동작구\s*/, '');
}

export function addZoneMarker(zone, type = 'danger') {
    const iconHtml = type === 'crosswalk' 
        ? '<span style="font-size:20px">🚦</span>'
        : '<span style="font-size:22px">⚠️</span>';
    
    const icon = L.divIcon({
        className: 'zone-marker',
        html: iconHtml,
        iconSize: type === 'crosswalk' ? [20, 20] : [22, 22],
        iconAnchor: type === 'crosswalk' ? [10, 10] : [11, 11]
    });
    
    const marker = L.marker([zone.lat, zone.lng], { icon, zIndexOffset: 1000 }).addTo(window.map);
    marker.zoneData = zone;
    
    const displayLocation = cleanLocation(zone.location);
    const popupContent = type === 'crosswalk'
        ? `<div class="zone-popup"><h3>🚦 ${zone.name || displayLocation}</h3></div>`
        : `<div class="zone-popup"><h3>🚨 ${displayLocation}</h3><div>사고: ${zone.accidents || 0}건</div><div>사망: ${zone.casualties || 0}명</div></div>`;
    
    marker.bindPopup(popupContent);
}

export function updateZonePanel() {
    const zoneList = document.getElementById('zone-list');
    const zoneCount = document.getElementById('zone-count');
    
    if (!zoneList || !zoneCount) return;
    
    zoneCount.textContent = childSafetyZones.length;
    
    if (childSafetyZones.length === 0) {
        zoneList.innerHTML = '<div class="zone-item">데이터 로딩 중...</div>';
        return;
    }
    
    const center = window.userLocation || APP_CONFIG.DEFAULT_LOCATION;
    const zonesWithDistance = childSafetyZones.map(zone => ({
        ...zone,
        distance: getDistance(center.lat, center.lng, zone.lat, zone.lng)
    })).sort((a, b) => a.distance - b.distance);
    
    zoneList.innerHTML = '';
    zonesWithDistance.slice(0, 10).forEach(zone => {
        const item = document.createElement('div');
        item.className = 'zone-item';
        const displayName = zone.name || cleanLocation(zone.location) || '알 수 없는 위치';
        const icon = zone.isCrosswalk ? '🚦' : '⚠️';
        const borderColor = zone.isCrosswalk ? '#ffc107' : '#e74c3c';
        item.style.borderLeftColor = borderColor;
        item.style.background = zone.isCrosswalk ? '#fffef0' : '#fff3f0';
        item.innerHTML = `<span class="zone-icon">${icon}</span><span class="zone-name">${displayName}</span><span class="zone-distance">${formatDistance(zone.distance)}</span>`;
        item.addEventListener('click', () => window.map?.setView([zone.lat, zone.lng], 16));
        zoneList.appendChild(item);
    });
    
    updateConnectingLines(zonesWithDistance.slice(0, 5));
}

export function formatDistance(meters) {
    if (meters >= 1000) {
        return (meters / 1000).toFixed(1) + 'km';
    }
    return Math.round(meters) + 'm';
}

function updateConnectingLines(nearestZones) {
    if (!window.map) return;
    
    connectingLines.forEach(line => window.map.removeLayer(line));
    connectingLines = [];
    
    const loc = window.userLocation || APP_CONFIG.DEFAULT_LOCATION;
    
    nearestZones.forEach(zone => {
        const line = L.polyline([
            [loc.lat, loc.lng],
            [zone.lat, zone.lng]
        ], {
            color: '#e74c3c',
            weight: 1.5,
            dashArray: '4, 4',
            opacity: 0.6
        }).addTo(window.map);
        
        connectingLines.push(line);
        
        const midLat = (loc.lat + zone.lat) / 2;
        const midLng = (loc.lng + zone.lng) / 2;
        
        const label = L.divIcon({
            className: 'distance-label',
            html: `<div style="background:white;padding:2px 4px;border-radius:3px;font-size:10px;border:1px solid #e74c3c">${formatDistance(zone.distance)}</div>`,
            iconSize: [50, 20],
            iconAnchor: [25, 10]
        });
        
        const marker = L.marker([midLat, midLng], { icon: label }).addTo(window.map);
        connectingLines.push(marker);
    });
}