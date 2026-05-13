// js/settingsPanel.js - 지도 설정 패널 (아이콘/색상 커스터마이징 + 데이터 업데이트)
import { loadSettings, saveSettings, ICON_CONFIG } from './config.js';
import { initUploadUI } from './dataUploader.js';

const ICON_SET = ['S', 'M', 'H', 'K', 'C', 'A', 'T', 'W', 'P', 'B', '★', '●', '▲', '■', '◆', '♥', '✦', '⚠', '☀', '♻'];
const COLOR_PALETTE = [
    '#e74c3c', '#e91e63', '#9b59b6', '#673ab7',
    '#3f51b5', '#2196f3', '#00bcd4', '#009688',
    '#4caf50', '#8bc34a', '#ffeb3b', '#ff9800',
    '#ff5722', '#795548', '#9e9e9e', '#2c3e50'
];

const CATEGORY_LABELS = {
    school_elem: '초등학교',
    school_middle: '중학교',
    school_high: '고등학교',
    kindergarten: '유치원',
    childcare: '어린이집',
    academy: '학원',
    special_school: '특수학교',
    protection_zone: '어린이보호구역',
    crosswalk: '횡단보도',
    accident_zone: '사고다발지역'
};

let panelEl = null;
let activePicker = null;

export function openSettingsPanel() {
    closeSettingsPanel();
    const panel = document.createElement('div');
    panel.id = 'settings-panel-modal';
    panel.style.cssText = `
        position:fixed;top:0;left:0;right:0;bottom:0;z-index:2000;
        background:rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;
    `;
    panel.addEventListener('click', e => { if (e.target === panel) closeSettingsPanel(); });

    const box = document.createElement('div');
    box.style.cssText = `
        background:white;border-radius:12px;width:400px;max-height:90vh;
        overflow-y:auto;padding:20px;box-shadow:0 10px 40px rgba(0,0,0,0.3);
    `;
    box.innerHTML = buildSettingsHTML();
    panel.appendChild(box);
    document.body.appendChild(panel);
    panelEl = panel;
    bindEvents(box);
}

export function closeSettingsPanel() {
    if (panelEl) { panelEl.remove(); panelEl = null; }
    if (activePicker) { activePicker.remove(); activePicker = null; }
}

function buildSettingsHTML() {
    const settings = loadSettings();
    const icons = settings.icons || ICON_CONFIG;

    let rows = '';
    for (const [key, label] of Object.entries(CATEGORY_LABELS)) {
        const cfg = icons[key] || ICON_CONFIG[key];
        rows += `
            <tr data-key="${key}">
                <td><input type="checkbox" class="vis-cb" ${cfg.visible !== false ? 'checked' : ''}></td>
                <td class="cat-label">${label}</td>
                <td><span class="icon-preview" style="background:${cfg.color};color:#fff;border-radius:50%;display:inline-block;width:28px;height:28px;text-align:center;line-height:28px;font-weight:bold;font-size:13px;cursor:pointer;">${cfg.icon}</span></td>
                <td><span class="color-dot" style="background:${cfg.color};border:2px solid #ddd;border-radius:50%;display:inline-block;width:22px;height:22px;cursor:pointer;"></span></td>
            </tr>`;
    }

    return `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <h2 style="margin:0;font-size:18px;color:#2c3e50;">⚙️ 지도 설정</h2>
            <button id="settings-close" style="background:none;border:none;font-size:22px;cursor:pointer;color:#999;">&times;</button>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead><tr style="border-bottom:2px solid #3498db;">
                <th style="width:30px;padding:6px;">표시</th>
                <th style="text-align:left;padding:6px;">카테고리</th>
                <th style="width:60px;padding:6px;">아이콘</th>
                <th style="width:50px;padding:6px;">색상</th>
            </tr></thead>
            <tbody>${rows}</tbody>
        </table>
        <div style="margin-top:16px;display:flex;gap:8px;justify-content:flex-end;">
            <button id="settings-reset" style="background:#95a5a6;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;">🔄 기본값</button>
            <button id="settings-apply" style="background:#3498db;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;">✅ 적용</button>
        </div>
        <div id="upload-ui-container"></div>
    `;
}

function bindEvents(box) {
    box.querySelector('#settings-close').onclick = closeSettingsPanel;
    box.querySelector('#settings-apply').onclick = applySettings;
    box.querySelector('#settings-reset').onclick = resetSettings;

    // 아이콘 피커
    box.querySelectorAll('.icon-preview').forEach(el => {
        el.onclick = e => {
            e.stopPropagation();
            openIconPicker(el);
        };
    });

    // 색상 피커
    box.querySelectorAll('.color-dot').forEach(el => {
        el.onclick = e => {
            e.stopPropagation();
            openColorPicker(el);
        };
    });

    // 업로드 UI 초기화
    const uploadContainer = box.querySelector('#upload-ui-container');
    if (uploadContainer) {
        initUploadUI(uploadContainer);
    }
}

function openIconPicker(target) {
    closePickers();
    const rect = target.getBoundingClientRect();
    const picker = document.createElement('div');
    picker.className = 'icon-picker-popup';
    picker.style.cssText = `
        position:fixed;top:${rect.bottom + 4}px;left:${rect.left}px;
        background:white;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.2);
        padding:8px;display:grid;grid-template-columns:repeat(5,1fr);gap:4px;z-index:3000;
    `;
    ICON_SET.forEach(ic => {
        const btn = document.createElement('button');
        const bg = window.getComputedStyle(target).backgroundColor;
        btn.textContent = ic;
        btn.style.cssText = `width:36px;height:36px;border-radius:50%;border:2px solid transparent;background:${bg};color:#fff;font-weight:bold;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:center;`;
        btn.onclick = () => {
            target.textContent = ic;
            const tr = target.closest('tr');
            if (tr) saveRowState(tr);
            closePickers();
        };
        picker.appendChild(btn);
    });
    document.body.appendChild(picker);
    activePicker = picker;

    document.addEventListener('click', closePickersHandler, { once: true });
}

function openColorPicker(target) {
    closePickers();
    const rect = target.getBoundingClientRect();
    const picker = document.createElement('div');
    picker.className = 'color-picker-popup';
    picker.style.cssText = `
        position:fixed;top:${rect.bottom + 4}px;left:${rect.left}px;
        background:white;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.2);
        padding:8px;display:grid;grid-template-columns:repeat(4,1fr);gap:4px;z-index:3000;
    `;
    COLOR_PALETTE.forEach(c => {
        const btn = document.createElement('button');
        btn.style.cssText = `width:32px;height:32px;border-radius:50%;border:2px solid #ddd;background:${c};cursor:pointer;`;
        btn.onclick = () => {
            target.style.background = c;
            const tr = target.closest('tr');
            const preview = tr.querySelector('.icon-preview');
            if (preview) preview.style.background = c;
            saveRowState(tr);
            closePickers();
        };
        picker.appendChild(btn);
    });
    document.body.appendChild(picker);
    activePicker = picker;

    document.addEventListener('click', closePickersHandler, { once: true });
}

function closePickers() {
    if (activePicker) { activePicker.remove(); activePicker = null; }
}

function closePickersHandler() { closePickers(); }

function saveRowState(tr) {
    const preview = tr.querySelector('.icon-preview');
    const dot = tr.querySelector('.color-dot');
    const icon = preview.textContent;
    const color = dot.style.background || '#999';
    preview.style.background = color;
}

function collectSettings() {
    const settings = {};
    document.querySelectorAll('#settings-panel-modal table tbody tr').forEach(tr => {
        const key = tr.dataset.key;
        if (!key) return;
        const cb = tr.querySelector('.vis-cb');
        const preview = tr.querySelector('.icon-preview');
        const dot = tr.querySelector('.color-dot');
        settings[key] = {
            visible: cb.checked,
            icon: preview.textContent,
            color: dot.style.background || '#999'
        };
    });
    return settings;
}

function applySettings() {
    const icons = collectSettings();
    const cfg = loadSettings();
    cfg.icons = icons;
    saveSettings(cfg);
    closeSettingsPanel();
    location.reload(); // 지도 다시 그림
}

function resetSettings() {
    saveSettings({ icons: {} }); // config.js 기본값 사용
    closeSettingsPanel();
    location.reload();
}
