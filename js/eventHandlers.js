// js/eventHandlers.js - 이벤트 리스너
import { APP_CONFIG } from './config.js';
import { requestLocation, updateUserLocation, updateUserCircle } from './userLocation.js';
import { updateAlertButton, updateCautionButton, dismissAlert } from './alertSystem.js';

let testMode = false;

export function setupEventListeners() {
    console.log('[Events] setupEventListeners 실행');
    
    const dangerSlider = document.getElementById('danger-slider');
    const dangerValue = document.getElementById('danger-value');
    const cautionSlider = document.getElementById('caution-slider');
    const cautionValue = document.getElementById('caution-value');
    
    dangerSlider?.addEventListener('input', (e) => {
        APP_CONFIG.DANGER_RADIUS = parseInt(e.target.value);
        dangerValue.textContent = e.target.value + 'm';
        localStorage.setItem('dangerRadius', APP_CONFIG.DANGER_RADIUS);
        updateUserCircle();
    });
    
    cautionSlider?.addEventListener('input', (e) => {
        APP_CONFIG.CAUTION_RADIUS = parseInt(e.target.value);
        cautionValue.textContent = e.target.value + 'm';
        localStorage.setItem('cautionRadius', APP_CONFIG.CAUTION_RADIUS);
        updateUserCircle();
    });
    
    document.getElementById('btn-locate')?.addEventListener('click', requestLocation);
    
    document.getElementById('btn-alert')?.addEventListener('click', () => {
        const btn = document.getElementById('btn-alert');
        btn?.classList.toggle('off');
        updateAlertButton();
    });
    
    document.getElementById('btn-caution')?.addEventListener('click', () => {
        const btn = document.getElementById('btn-caution');
        btn?.classList.toggle('off');
        updateCautionButton();
        updateUserCircle();
    });
    
    document.getElementById('btn-test-mode')?.addEventListener('click', () => {
        testMode = !testMode;
        document.getElementById('test-mode-checkbox').checked = testMode;
        
        if (window.userMarker) {
            if (testMode) {
                window.userMarker.dragging.enable();
                window.userMarker.getElement()?.classList.add('test-mode');
            } else {
                window.userMarker.dragging.disable();
                window.userMarker.getElement()?.classList.remove('test-mode');
                requestLocation();
            }
        }
    });
    
    document.getElementById('btn-dismiss-alert')?.addEventListener('click', dismissAlert);
    
    document.getElementById('test-mode-checkbox')?.addEventListener('change', (e) => {
        testMode = e.target.checked;
        if (window.userMarker) {
            testMode ? window.userMarker.dragging.enable() : window.userMarker.dragging.disable();
        }
    });
    
    document.addEventListener('keydown', e => {
        if (testMode && e.key === 'Escape') {
            testMode = false;
            document.getElementById('test-mode-checkbox').checked = false;
        }
    });
    
    document.getElementById('sidebar-toggle')?.addEventListener('click', () => {
        document.getElementById('sidebar')?.classList.toggle('active');
    });
}

export function handleMapClick(e) {
    console.log('[Events] handleMapClick');
    if (testMode) {
        updateUserLocation(e.latlng.lat, e.latlng.lng);
    }
}

export function handleMapMoveEnd() {
    // 필요시 구현
}

export function handleUserMarkerDrag(e) {
    const pos = e.target.getLatLng();
    updateUserLocation(pos.lat, pos.lng);
}