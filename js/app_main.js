// js/app_main.js - 메인 진입점
import { initDOM, loadSettings, APP_CONFIG } from './config.js';
import { initMap, createUserMarker, setupMapEvents } from './mapInit.js';
import { loadZones, loadCrosswalks } from './dataLoader.js';
import { setupEventListeners, handleMapClick, handleMapMoveEnd } from './eventHandlers.js';
import { updateUserCircle } from './userLocation.js';
import { updateAlertButton, updateCautionButton } from './alertSystem.js';
import { updateZonePanel } from './zoneManager.js';
import { startMission } from './missionSystem.js';
import { openSettingsPanel } from './settingsPanel.js';

console.log('[App] 시작');

async function init() {
    console.log('[App] init() 실행');
    
    initDOM();
    loadSettings();
    
    window.userLocation = { ...APP_CONFIG.DEFAULT_LOCATION };
    
    initMap();
    console.log('[App] 지도 초기화 완료');
    
    setupMapEvents(handleMapClick, handleMapMoveEnd);
    createUserMarker();
    console.log('[App] 마커 생성 완료');
    
    setupEventListeners();
    updateAlertButton();
    updateCautionButton();
    
    try {
        await loadZones();
        console.log('[App] 데이터 로드 완료');
        
        updateUserCircle();
        updateZonePanel();
        console.log('[App] 섹터 원, 패널 업데이트 완료');
    } catch (err) {
        console.error('[App] 초기화 중 오류:', err);
    }
    
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            document.getElementById('sidebar')?.classList.toggle('active');
        });
    }

    document.getElementById('btn-settings')?.addEventListener('click', openSettingsPanel);
    
    fetch('http://localhost:5000/api/status')
        .then(r => r.json())
        .then(data => {
            if (data.server_ok) console.log('[Server] 업로드 서버 연결됨');
        })
        .catch(() => console.log('[Server] 업로드 서버 꺼짐 (python server.py 필요)'));

    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    console.log('[App] 초기화 완료');
}

document.addEventListener('DOMContentLoaded', init);