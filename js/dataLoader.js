// js/dataLoader.js - 데이터 로드
import { childSafetyZones, ICON_CONFIG } from './config.js';
import { addZoneMarker, updateZonePanel } from './zoneManager.js';

let cachedLocations = null;

function loadLocations() {
    if (cachedLocations) return Promise.resolve(cachedLocations);
    return fetch('data/locations.json')
        .then(res => {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.json();
        })
        .then(data => {
            cachedLocations = data;
            return data;
        });
}

const SUBCAT_TO_KEY = {
    '초등학교': 'school_elem',
    '중학교': 'school_middle',
    '고등학교': 'school_high',
    '유치원(일반)': 'kindergarten',
    '유치원(병설)': 'kindergarten',
    '유치원': 'kindergarten',
    '어린이집': 'childcare',
    '학원': 'academy',
    '특수학교': 'special_school'
};

function getIconCfg(category, subcategory) {
    const key = category === 'accident_zone' ? 'accident_zone'
        : category === 'protection_zone' ? 'protection_zone'
        : category === 'crosswalk' ? 'crosswalk'
        : SUBCAT_TO_KEY[subcategory] || 'school_elem';
    return ICON_CONFIG[key] || ICON_CONFIG.school_elem;
}

export function loadZones() {
    console.log('[Data] loadZones 실행');

    return loadLocations()
        .then(data => {
            const items = data.items || [];

            // 사고다발지역 마커
            items.filter(x => x.category === 'accident_zone').forEach(area => {
                if (area.lat && area.lng) {
                    const cfg = getIconCfg('accident_zone');
                    const zone = {
                        lat: area.lat,
                        lng: area.lng,
                        location: area.name,
                        accidents: area.properties?.accident_count || 0,
                        casualties: area.properties?.casualties || 0,
                        isCrosswalk: false
                    };
                    childSafetyZones.push(zone);
                    if (cfg.visible !== false) addZoneMarker(zone, 'danger');
                }
            });

            // 보호구역 표시
            loadProtectionZones(items);
            // 학교 마커
            loadSchoolMarkers(items);
            // 안전등급 마커
            loadSchoolSafetyGrades();
            // 횡단보도
            loadCrosswalks();
            // 테이블 채움
            fillTables(items);

            const statusEl = document.getElementById('status-text');
            if (statusEl) {
                statusEl.textContent = `사고 ${childSafetyZones.filter(z => !z.isCrosswalk).length}개, 횡단보도 ${childSafetyZones.filter(z => z.isCrosswalk).length}개`;
            }

            return data;
        })
        .catch(err => {
            console.error('[Data] 로드 실패:', err);
            const statusEl = document.getElementById('status-text');
            if (statusEl) {
                statusEl.textContent = '데이터 로드 실패: ' + err.message;
            }
            throw err;
        });
}

function loadProtectionZones(items) {
    const zones = items.filter(x => x.category === 'protection_zone' && x.lat && x.lng);
    const cfg = getIconCfg('protection_zone');
    if (cfg.visible === false) return;

    zones.forEach(z => {
        const p = z.properties || {};
        L.circle([z.lat, z.lng], {
            color: cfg.color,
            fillColor: cfg.color,
            fillOpacity: 0.12,
            radius: 50,
            weight: 2
        }).addTo(window.map).bindPopup(
            `<b>${z.name}</b><br>유형: ${z.subcategory}<br>📹 CCTV: ${p.cctv_count || 'N/A'}대<br>제한속도: ${p.speed_limit || 'N/A'}`
        );
        if (p.cctv_yn === 'Y' || (p.cctv_count || 0) > 0) {
            L.circleMarker([z.lat, z.lng], {
                radius: 5, color: cfg.color,
                fillColor: '#fff', fillOpacity: 0.9, weight: 2
            }).addTo(window.map);
        }
    });
    console.log('[Data] 보호구역:', zones.length, '개 표시');
}

function loadSchoolMarkers(items) {
    const cats = ['school', 'kindergarten', 'childcare', 'academy', 'special_school'];
    const schools = items.filter(x => cats.includes(x.category) && x.lat && x.lng);

    schools.forEach(school => {
        const cfg = getIconCfg(school.category, school.subcategory);
        if (cfg.visible === false) return;

        const divIcon = L.divIcon({
            className: 'safety-marker-dynamic',
            html: `<div style="width:24px;height:24px;border-radius:50%;background:${cfg.color};color:#fff;text-align:center;line-height:24px;font-weight:bold;font-size:11px;">${cfg.icon}</div>`,
            iconSize: [24, 24]
        });
        L.marker([school.lat, school.lng], { icon: divIcon })
            .addTo(window.map)
            .bindPopup(`<b>${school.name}</b><br>${school.subcategory}<br>${school.address}`);
    });
    console.log('[Data] 학교 마커:', schools.length, '개 표시');
}

export function loadSchoolSafetyGrades() {
    console.log('[Data] loadSchoolSafetyGrades 실행');

    fetch('data/analysis/school_safety_grades.json')
        .then(res => res.json())
        .then(data => {
            if (!data.safety_grades) return;

            data.safety_grades.forEach(item => {
                const gradeClass = `grade-${item.safety_grade}`;
                const gradeIcon = L.divIcon({
                    className: `safety-marker ${gradeClass}`,
                    html: item.safety_grade,
                    iconSize: [24, 24]
                });

                L.marker([item.lat, item.lng], { icon: gradeIcon })
                    .addTo(window.map)
                    .bindPopup(`<b>${item.school_name}</b><br>안전등급: <b>${item.safety_grade}</b><br>횡단보도: ${item.crosswalk_count}개<br>신호등비율: ${item.signal_ratio}`);
            });
        })
        .catch(err => console.error('[Data] 안전등급 로드 실패:', err));
}

export function loadCrosswalks() {
    console.log('[Data] loadCrosswalks 실행');

    const cfg = getIconCfg('crosswalk');
    if (cfg.visible === false) return;

    fetch('data/analysis/accessibility_score.json')
        .then(res => res.json())
        .then(data => {
            if (!data.accessibility_scores) return;

            let count = 0;
            data.accessibility_scores.forEach(cw => {
                if (cw.lat && cw.lng) {
                    const zone = {
                        lat: cw.lat,
                        lng: cw.lng,
                        name: `횡단보도 (${cw.grade})`,
                        isCrosswalk: true
                    };
                    childSafetyZones.push(zone);
                    addZoneMarker(zone, 'crosswalk');
                    count++;
                }
            });

            console.log('[Data] 횡단보도 마커:', count, '개 추가');
            updateZonePanel();

            const statusEl = document.getElementById('status-text');
            if (statusEl) {
                statusEl.textContent = `사고 ${childSafetyZones.filter(z => !z.isCrosswalk).length}개, 횡단보도 ${count}개`;
            }
        })
        .catch(err => console.error('[Data] 횡단보도 로드 실패:', err));
}

export function fillTables(items) {
    console.log('[Data] fillTables 실행');

    const schools = items.filter(x =>
        x.category === 'school' || x.category === 'kindergarten' ||
        x.category === 'childcare' || x.category === 'special_school'
    );

    const accidentAreas = items.filter(x => x.category === 'accident_zone');

    fetch('data/analysis/school_safety_grades.json')
        .then(res => res.json())
        .then(safetyData => {
            const safetyMap = {};
            if (safetyData.safety_grades) {
                safetyData.safety_grades.forEach(item => {
                    safetyMap[item.school_name] = item;
                });
            }

            const schoolTbody = document.getElementById('school-tbody');
            if (schoolTbody && schools.length > 0) {
                schoolTbody.innerHTML = '';
                schools.forEach(school => {
                    if (school.lat && school.lng) {
                        const info = safetyMap[school.name];
                        const tr = document.createElement('tr');
                        tr.innerHTML = `<td>${school.name}</td><td>${school.subcategory || ''}</td><td>${info?.signal_ratio?.toFixed(2) || 'N/A'}</td>`;
                        schoolTbody.appendChild(tr);
                    }
                });
            }

            const accidentTbody = document.getElementById('accident-tbody');
            if (accidentTbody && accidentAreas.length > 0) {
                accidentTbody.innerHTML = '';
                accidentAreas.forEach(area => {
                    const tr = document.createElement('tr');
                    const loc = (area.name || '').replace(/^서울특별시\s*/, '').replace(/^동작구\s*/, '');
                    tr.innerHTML = `<td>${loc}</td><td>${area.properties?.accident_count || 0}</td><td>${area.properties?.casualties || 0}</td>`;
                    accidentTbody.appendChild(tr);
                });
            }
        })
        .catch(err => console.error('[Data] 테이블 로드 실패:', err));
}
