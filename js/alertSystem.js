// js/alertSystem.js - 알림 시스템
import { APP_CONFIG } from './config.js';

let lastAlertTime = 0;
let lastCautionTime = 0;

export function showAlert(zone, distance, type) {
    const now = Date.now();
    const cooldown = APP_CONFIG.ALERT_COOLDOWN;
    
    if (type === 'danger' && now - lastAlertTime < cooldown) return;
    if (type === 'caution' && now - lastCautionTime < cooldown) return;
    
    if (type === 'danger') {
        lastAlertTime = now;
    } else {
        lastCautionTime = now;
    }
    
    const alertBanner = document.getElementById('alert-banner');
    const alertZoneName = document.getElementById('alert-zone-name');
    
    if (alertZoneName) {
        alertZoneName.textContent = `${zone.location || zone.name} (${Math.round(distance)}m)`;
    }
    
    if (alertBanner) {
        alertBanner.style.display = 'flex';
        alertBanner.style.background = type === 'danger' ? '#ffeb3b' : '#fff3cd';
        alertBanner.style.borderColor = type === 'danger' ? '#f39c12' : '#ffc107';
    }
    
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(
            type === 'danger' ? '🔴 경고 구역 진입!' : '⚠️ 주의 구역 접근',
            { body: `${zone.location || zone.name}까지 ${Math.round(distance)}m` }
        );
    }
    
    if ('vibrate' in navigator) {
        navigator.vibrate(type === 'danger' ? [300, 150, 300] : [150, 75, 150]);
    }
}

export function dismissAlert() {
    const alertBanner = document.getElementById('alert-banner');
    if (alertBanner) {
        alertBanner.style.display = 'none';
    }
}

export function updateAlertButton() {
    const btn = document.getElementById('btn-alert');
    if (!btn) return;
    
    const isOff = btn.classList.contains('off');
    btn.textContent = isOff ? '🔕 경고' : '🔔 경고';
}

export function updateCautionButton() {
    const btn = document.getElementById('btn-caution');
    if (!btn) return;
    
    const isOff = btn.classList.contains('off');
    btn.textContent = isOff ? '🔕 주의' : '⚠️ 주의';
}