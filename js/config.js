// js/config.js - 설정 및 유틸리티
export const APP_CONFIG = {
    DANGER_RADIUS: 15,
    CAUTION_RADIUS: 100,
    LOCATION_OPTIONS: { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 },
    CHECK_INTERVAL: 3000,
    ALERT_COOLDOWN: 10000,
    DEFAULT_LOCATION: { lat: 37.5024, lng: 126.9517 }
};

export const ICON_CONFIG = {
    school_elem:    { icon: 'S', color: '#27ae60', visible: true },
    school_middle:  { icon: 'M', color: '#2980b9', visible: true },
    school_high:    { icon: 'H', color: '#8e44ad', visible: true },
    kindergarten:   { icon: 'K', color: '#f39c12', visible: true },
    childcare:      { icon: 'C', color: '#e67e22', visible: true },
    academy:        { icon: 'A', color: '#95a5a6', visible: true },
    special_school: { icon: '★', color: '#e74c3c', visible: true },
    protection_zone:{ icon: '●', color: '#9b59b6', visible: true },
    crosswalk:      { icon: '·', color: '#bdc3c7', visible: true },
    accident_zone:  { icon: '⚠', color: '#e74c3c', visible: true }
};

export const childSafetyZones = [];

export function getElement(id) {
    return document.getElementById(id);
}

export function initDOM() {
    console.log('[Config] initDOM 실행');
}

export function loadSettings() {
    const savedDanger = localStorage.getItem('dangerRadius');
    if (savedDanger) APP_CONFIG.DANGER_RADIUS = parseInt(savedDanger);

    const savedCaution = localStorage.getItem('cautionRadius');
    if (savedCaution) APP_CONFIG.CAUTION_RADIUS = parseInt(savedCaution);

    const savedIcons = localStorage.getItem('kidsSafeIcons');
    if (savedIcons) {
        try {
            const parsed = JSON.parse(savedIcons);
            Object.assign(ICON_CONFIG, parsed);
        } catch (e) {
            console.warn('[Config] 아이콘 설정 파싱 실패:', e);
        }
    }
}

export function saveSettings(cfg) {
    if (cfg.icons) {
        localStorage.setItem('kidsSafeIcons', JSON.stringify(cfg.icons));
    }
    if (cfg.dangerRadius) {
        localStorage.setItem('dangerRadius', cfg.dangerRadius);
        APP_CONFIG.DANGER_RADIUS = cfg.dangerRadius;
    }
    if (cfg.cautionRadius) {
        localStorage.setItem('cautionRadius', cfg.cautionRadius);
        APP_CONFIG.CAUTION_RADIUS = cfg.cautionRadius;
    }
}
