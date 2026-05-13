// js/userLocation.js - 위치 관련 함수
import { APP_CONFIG, childSafetyZones } from './config.js';
import { showAlert, dismissAlert } from './alertSystem.js';
import { startMission } from './missionSystem.js';

let heading = 0;
let prevLocation = null;
let watchId = null;
let dangerCircle = null;
let cautionCircle = null;

window.inDangerZone = false;
window.inCrosswalk = false;

export function requestLocation() {
    console.log('[Location] requestLocation 실행');
    
    if (!navigator.geolocation) {
        updateStatus('위치 서비스 미지원');
        return;
    }
    
    updateStatus('위치 검색 중...');
    
    navigator.geolocation.getCurrentPosition(
        pos => updateUserLocation(pos.coords.latitude, pos.coords.longitude),
        err => {
            console.error('[Location] 오류:', err);
            updateStatus('위치 검색 실패');
        },
        APP_CONFIG.LOCATION_OPTIONS
    );
}

export function updateUserLocation(lat, lng) {
    console.log('[Location] updateUserLocation:', lat, lng);
    
    if (window.userLocation && prevLocation) {
        const dist = getDistance(window.userLocation.lat, window.userLocation.lng, lat, lng);
        if (dist > 5) {
            heading = getBearing(window.userLocation.lat, window.userLocation.lng, lat, lng);
        }
    }
    prevLocation = window.userLocation;
    window.userLocation = { lat, lng };
    
    if (window.userMarker) {
        window.userMarker.setLatLng([lat, lng]);
    }
    
    const testMode = document.getElementById('test-mode-checkbox')?.checked;
    if (!testMode && window.map) {
        const zoom = window.map.getZoom();
        window.map.setView([lat, lng], zoom > 14 ? zoom : 15);
    }
    
    updateUserCircle();
    checkProximity();
    updateStatus(`위치: ${lat.toFixed(4)}, ${lng.toFixed(4)}`);
    startWatching();
}

export function updateUserCircle() {
    if (!window.map) return;
    
    if (dangerCircle) window.map.removeLayer(dangerCircle);
    if (cautionCircle) window.map.removeLayer(cautionCircle);
    
    const loc = window.userLocation || APP_CONFIG.DEFAULT_LOCATION;
    const angleDeg = heading * 180 / Math.PI;
    
    dangerCircle = L.sector([loc.lat, loc.lng], {
        radius: APP_CONFIG.DANGER_RADIUS,
        startAngle: angleDeg - 15,
        endAngle: angleDeg + 15,
        color: '#e74c3c',
        fillColor: '#e74c3c',
        fillOpacity: 0.15,
        weight: 2,
        dashArray: '5, 5'
    }).addTo(window.map);
    
    cautionCircle = L.sector([loc.lat, loc.lng], {
        radius: APP_CONFIG.CAUTION_RADIUS,
        startAngle: angleDeg - 15,
        endAngle: angleDeg + 15,
        color: '#ffc107',
        fillColor: '#ffc107',
        fillOpacity: 0.1,
        weight: 2,
        dashArray: '8, 4'
    }).addTo(window.map);
}

export function checkProximity() {
    if (!window.userLocation) return;
    
    let nearestDanger = null;
    let minDangerDist = Infinity;
    let nearestCaution = null;
    let minCautionDist = Infinity;
    
    childSafetyZones.forEach(zone => {
        if (!zone.lat || !zone.lng) return;
        
        const dist = getDistance(window.userLocation.lat, window.userLocation.lng, zone.lat, zone.lng);
        
        if (zone.isCrosswalk) {
            if (dist <= APP_CONFIG.CAUTION_RADIUS && dist < minCautionDist) {
                minCautionDist = dist;
                nearestCaution = zone;
            }
        } else {
            if (dist <= APP_CONFIG.DANGER_RADIUS && dist < minDangerDist) {
                minDangerDist = dist;
                nearestDanger = zone;
            }
        }
    });
    
    const btnAlert = document.getElementById('btn-alert');
    const isAlertOn = btnAlert && !btnAlert.classList.contains('off');
    
    const btnCaution = document.getElementById('btn-caution');
    const isCautionOn = btnCaution && !btnCaution.classList.contains('off');
    
    if (nearestDanger) {
        if (isAlertOn) showAlert(nearestDanger, minDangerDist, 'danger');
        if (!window.inDangerZone && minDangerDist <= APP_CONFIG.DANGER_RADIUS) {
            window.inDangerZone = true;
            startMission(nearestDanger);
        }
    } else if (nearestCaution) {
        if (isCautionOn) showAlert(nearestCaution, minCautionDist, 'caution');
        if (minCautionDist <= APP_CONFIG.DANGER_RADIUS) {
            if (!window.inCrosswalk) {
                window.inCrosswalk = true;
                startMission(nearestCaution);
            }
        } else {
            window.inCrosswalk = false;
        }
    } else {
        if (!nearestDanger) window.inDangerZone = false;
        if (!nearestCaution) window.inCrosswalk = false;
        dismissAlert();
    }
    
    const distDisplay = document.getElementById('distance-display');
    if (distDisplay) {
        if (nearestDanger) {
            distDisplay.textContent = `⚠️ ${Math.round(minDangerDist)}m`;
        } else if (nearestCaution) {
            distDisplay.textContent = `🚦 ${Math.round(minCautionDist)}m`;
        } else {
            distDisplay.textContent = '';
        }
    }
}

export function getDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;
    
    const a = Math.sin(Δφ / 2) ** 2 + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function getBearing(lat1, lon1, lat2, lon2) {
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;
    
    const y = Math.sin(Δλ) * Math.cos(φ2);
    const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
    return Math.atan2(y, x);
}

export function startWatching() {
    if (watchId) return;
    
    watchId = navigator.geolocation.watchPosition(
        pos => updateUserLocation(pos.coords.latitude, pos.coords.longitude),
        err => console.error('[Location] 추적 오류:', err),
        APP_CONFIG.LOCATION_OPTIONS
    );
}

function updateStatus(text) {
    const el = document.getElementById('status-text');
    if (el) el.textContent = text;
}