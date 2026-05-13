// js/mapInit.js - 지도 초기화
import { APP_CONFIG } from './config.js';
import { updateUserCircle, checkProximity } from './userLocation.js';

export function initMap() {
    console.log('[Map] initMap 실행');
    console.log('[Map] window.map 상태:', typeof window.map, window.map);
    
    if (window.map && typeof window.map.on === 'function') {
        console.log('[Map] 이미 초기화됨');
        return window.map;
    }
    
    const mapEl = document.getElementById('map');
    if (!mapEl) {
        console.error('[Map] map 요소 없음');
        return null;
    }
    
    console.log('[Map] Leaflet 상태:', typeof L, typeof L.map);
    
    window.map = L.map('map', { zoomControl: false }).setView([37.5024, 126.9517], 14);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors', maxZoom: 19
    }).addTo(window.map);
    
    L.control.zoom({ position: 'bottomright' }).addTo(window.map);
    
    addLegend();
    console.log('[Map] 지도 초기화 완료, window.map:', typeof window.map);
    return window.map;
}

function addLegend() {
    const legend = L.control({ position: 'topright' });
    legend.onAdd = function() {
        const div = L.DomUtil.create('div', 'legend');
        div.style.cssText = 'background:white;padding:8px;border-radius:6px;box-shadow:0 0 10px rgba(0,0,0,0.2);font-size:11px;line-height:1.7;';
        div.innerHTML = '<b>범례</b><br>' +
            '<span style="color:#27ae60">S</span> 초등학교<br>' +
            '<span style="color:#2980b9">M</span> 중학교<br>' +
            '<span style="color:#8e44ad">H</span> 고등학교<br>' +
            '<span style="color:#f39c12">K</span> 유치원<br>' +
            '<span style="color:#e67e22">C</span> 어린이집<br>' +
            '<span style="color:#95a5a6">A</span> 학원<br>' +
            '<span style="color:#e74c3c">★</span> 특수학교<br>' +
            '<span style="color:#9b59b6">●</span> 보호구역(CCTV)<br>' +
            '<span style="color:#e74c3c">⚠</span> 사고다발지역<br>' +
            '<span style="color:#bdc3c7">·</span> 횡단보도<br>' +
            '<span style="color:#27ae60">●</span> A <span style="color:#2ecc71">●</span> B <span style="color:#f1c40f">●</span> C ' +
            '<span style="color:#e67e22">●</span> D <span style="color:#e74c3c">●</span> F<br>' +
            '<span style="color:orange">🔥</span> 위험밀도(히트맵)';
        return div;
    };
    legend.addTo(window.map);
}

export function createUserMarker() {
    console.log('[Map] createUserMarker 실행, window.map:', typeof window.map);
    
    if (!window.map) {
        console.error('[Map] window.map이 null, 마커 생성 불가');
        return;
    }
    
    const loc = window.userLocation || APP_CONFIG.DEFAULT_LOCATION;
    const icon = L.divIcon({
        className: 'user-marker',
        html: '📍',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
    
    window.userMarker = L.marker([loc.lat, loc.lng], { icon, draggable: true, zIndexOffset: -1000 }).addTo(window.map);
    
    window.userMarker.on('dragend', e => {
        const pos = e.target.getLatLng();
        window.userLocation = { lat: pos.lat, lng: pos.lng };
        updateUserCircle();
        checkProximity();
    });
    
    console.log('[Map] 사용자 마커 생성 완료');
}

export function setupMapEvents(clickHandler, moveEndHandler) {
    console.log('[Map] setupMapEvents 호출, window.map:', typeof window.map);
    
    if (!window.map) {
        console.error('[Map] window.map이 null/undefined');
        return;
    }
    
    if (typeof window.map.on !== 'function') {
        console.error('[Map] window.map.on이 함수가 아님:', typeof window.map.on);
        return;
    }
    
    window.map.on('click', clickHandler);
    window.map.on('moveend', moveEndHandler);
    console.log('[Map] 이벤트 리스너 등록 완료');
}

// L.Sector for sector visualization
L.Sector = L.Circle.extend({
    options: { startAngle: 0, endAngle: 360 },
    buildPath: function() {
        const center = this._latlng;
        const radius = this._mRadius;
        const startAngle = this._startAngle * Math.PI / 180;
        const endAngle = this._endAngle * Math.PI / 180;
        this._point = this._map.latLngToContainerPoint(center);
        this._points = this._computePoints(center, radius, startAngle, endAngle);
    },
    _computePoints: function(center, radius, startAngle, endAngle) {
        const points = [];
        const angleStep = (endAngle - startAngle) / 30;
        for (let angle = startAngle; angle <= endAngle; angle += angleStep) {
            const dx = radius * Math.cos(angle - Math.PI / 2);
            const dy = radius * Math.sin(angle - Math.PI / 2);
            const point = this._map.containerPointToLatLng([this._point.x + dx, this._point.y + dy]);
            points.push(point);
        }
        return points;
    },
    getPathString: function() {
        if (!this._points || this._points.length === 0) return '';
        const center = this._point;
        let d = 'M ' + center.x + ' ' + center.y;
        for (let i = 0; i < this._points.length; i++) {
            const point = this._map.latLngToContainerPoint(this._points[i]);
            d += ' L ' + point.x + ' ' + point.y;
        }
        d += ' Z';
        return d;
    }
});

L.sector = function(latlng, options) {
    return new L.Sector(latlng, options);
};