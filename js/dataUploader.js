// js/dataUploader.js - 데이터 업로드 UI (4개 파일 슬롯)
const UPLOAD_SOURCES = [
    {
        key: 'schools',
        label: '학교별위치정보',
        icon: '🏫',
        fileLabel: '학교별위치정보_*.csv',
        expectedHeaders: ['학교코드', '학교코드명', '위도값', '경도값'],
        requiredHeaders: ['학교코드', '학교코드명']
    },
    {
        key: 'protection_zones',
        label: '어린이보호구역',
        icon: '🚸',
        fileLabel: '어린이보호구역_*.csv',
        expectedHeaders: ['시설종류', '대상시설명', '위도', '경도', '카메라 설치여부(CCTV)'],
        requiredHeaders: ['시설종류', '대상시설명']
    },
    {
        key: 'crosswalks',
        label: '횡단보도',
        icon: '🚦',
        fileLabel: '횡단보도_*.csv',
        expectedHeaders: ['횡단보도관리번호', '소재지도로명주소', '위도', '경도', '보행자신호등유무'],
        requiredHeaders: ['횡단보도관리번호']
    },
    {
        key: 'accidents',
        label: '사고다발지역',
        icon: '⚠️',
        fileLabel: '사고다발지역_*.csv',
        expectedHeaders: ['사고다발지역관리번호', '사고다발지역시도시군구', '위도', '경도', '사고건수'],
        requiredHeaders: ['사고다발지역관리번호']
    }
];

const SERVER_URL = 'http://localhost:5000';

let fileSelections = {}; // key -> { file, headers, status }
let serverConnected = false;

export function initUploadUI(container) {
    container.innerHTML = `
        <h3 style="margin:16px 0 8px;font-size:14px;color:#2c3e50;border-top:2px solid #eee;padding-top:12px;">
            📤 데이터 업데이트
        </h3>
        <div style="font-size:11px;color:#888;margin-bottom:8px;">
            서버 상태: <span id="server-status">🔍 확인중...</span>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
            <tbody id="upload-slots"></tbody>
        </table>
        <div style="margin-top:8px;display:flex;gap:6px;justify-content:flex-end;">
            <button id="btn-upload-start" disabled style="background:#27ae60;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:12px;">
                🔄 선택한 파일 업데이트
            </button>
        </div>
        <div id="upload-progress" style="margin-top:8px;display:none;">
            <div style="background:#eee;border-radius:4px;height:6px;">
                <div id="upload-progress-bar" style="width:0%;height:100%;background:#3498db;border-radius:4px;transition:width 0.5s;"></div>
            </div>
            <div id="upload-status-text" style="font-size:11px;color:#666;margin-top:4px;"></div>
        </div>
    `;

    renderSlots();
    checkServer();
    bindEvents();
}

function checkServer() {
    const el = document.getElementById('server-status');
    fetch(`${SERVER_URL}/api/status`)
        .then(r => r.json())
        .then(data => {
            serverConnected = true;
            el.textContent = '✅ 서버 연결됨';
            el.style.color = '#27ae60';
            // 파일별 개수 업데이트
            if (data.files) {
                UPLOAD_SOURCES.forEach(src => {
                    const info = data.files[src.key];
                    if (info && info.exists) {
                        const countEl = document.getElementById(`file-count-${src.key}`);
                        if (countEl) {
                            countEl.textContent = `✓ ${info.modified}`;
                            countEl.style.color = '#27ae60';
                        }
                    }
                });
            }
            document.getElementById('btn-upload-start').disabled = Object.keys(fileSelections).length === 0;
        })
        .catch(() => {
            serverConnected = false;
            el.textContent = '❌ 서버 꺼짐 (python server.py 실행 필요)';
            el.style.color = '#e74c3c';
        });
}

function renderSlots() {
    const tbody = document.getElementById('upload-slots');
    tbody.innerHTML = UPLOAD_SOURCES.map(src => `
        <tr>
            <td style="padding:6px 4px;white-space:nowrap;width:30px;">${src.icon}</td>
            <td style="padding:6px 4px;">
                <div style="font-weight:600;">${src.label}</div>
                <div style="font-size:10px;color:#999;">${src.fileLabel}</div>
            </td>
            <td style="padding:6px 4px;text-align:right;">
                <span id="file-status-${src.key}" style="font-size:11px;color:#999;">파일 선택 안됨</span>
            </td>
            <td style="padding:6px 4px;width:50px;text-align:right;">
                <button class="btn-upload-slot" data-key="${src.key}" style="background:#3498db;color:#fff;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:11px;">
                    📂 선택
                </button>
                <input type="file" id="file-input-${src.key}" accept=".csv" style="display:none;" data-key="${src.key}">
            </td>
        </tr>
    `).join('');
}

function bindEvents() {
    // 파일 선택 버튼
    document.querySelectorAll('.btn-upload-slot').forEach(btn => {
        btn.addEventListener('click', () => {
            const key = btn.dataset.key;
            document.getElementById(`file-input-${key}`).click();
        });
    });

    // 파일 input
    UPLOAD_SOURCES.forEach(src => {
        const input = document.getElementById(`file-input-${src.key}`);
        input.addEventListener('change', (e) => handleFileSelect(src.key, e));
    });

    // 업데이트 실행 버튼
    document.getElementById('btn-upload-start').addEventListener('click', executeUpload);
}

function handleFileSelect(key, event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        const lines = text.split('\n').filter(l => l.trim());
        if (lines.length < 2) {
            setFileStatus(key, '❌ 파일이 비어있음', '#e74c3c');
            return;
        }

        const headers = parseCSVLine(lines[0]);
        const source = UPLOAD_SOURCES.find(s => s.key === key);
        const result = validateHeaders(headers, source);

        if (result.match) {
            const dataLines = lines.slice(1).filter(l => l.trim());
            setFileStatus(key, `✅ ${dataLines.length}개, ${key} 감지됨 (${result.ratio}%)`, '#27ae60');
            fileSelections[key] = { file, headers, rowCount: dataLines.length };
        } else if (result.unknown) {
            // 정 반대: 자동감지
            autoDetectAndShow(key, headers, file, lines);
        } else {
            // 형식 불일치 → 덮어쓰기 안내
            showFormatMismatch(key, headers, source);
        }
        updateUploadButton();
    };
    reader.readAsText(file);
}

function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (ch === '"') { inQuotes = !inQuotes; continue; }
        if (ch === ',' && !inQuotes) { result.push(current.trim()); current = ''; continue; }
        current += ch;
    }
    result.push(current.trim());
    return result;
}

function validateHeaders(headers, source) {
    const required = source.requiredHeaders;
    const matched = required.filter(h => headers.includes(h)).length;
    const ratio = matched / required.length;

    if (ratio >= 0.6) {
        return { match: true, ratio: Math.round(ratio * 100), missing: required.filter(h => !headers.includes(h)) };
    }
    return { match: false, ratio: Math.round(ratio * 100), unknown: true };
}

function autoDetectAndShow(key, headers, file, lines) {
    // 서버에 검증 요청
    setFileStatus(key, '🔍 서버에서 형식 확인중...', '#f39c12');
    fetch(`${SERVER_URL}/api/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ headers })
    })
    .then(r => r.json())
    .then(result => {
        if (result.match && result.detected_as) {
            const dataLines = lines.slice(1).filter(l => l.trim());
            setFileStatus(key, `✅ ${dataLines.length}개, ${result.detected_as} 감지됨`, '#27ae60');
            fileSelections[key] = { file, headers, rowCount: dataLines.length, overrideKey: result.detected_as };
        } else {
            showFormatMismatch(key, headers, UPLOAD_SOURCES.find(s => s.key === key));
        }
    })
    .catch(() => {
        showFormatMismatch(key, headers, UPLOAD_SOURCES.find(s => s.key === key));
    });
}

function showFormatMismatch(key, headers, source) {
    // 기존 방식 선택 버튼 제공
    setFileStatus(key, `⚠️ 헤더 불일치 - 아래 중 선택하세요`, '#e74c3c');

    const statusEl = document.getElementById(`file-status-${key}`);
    const container = document.createElement('div');
    container.style.cssText = 'margin-top:4px;display:flex;gap:4px;flex-wrap:wrap;';

    UPLOAD_SOURCES.forEach(s => {
        const btn = document.createElement('button');
        btn.textContent = `${s.icon} ${s.label}`;
        btn.style.cssText = 'background:#ecf0f1;border:1px solid #bdc3c7;padding:2px 8px;border-radius:4px;cursor:pointer;font-size:10px;';
        btn.onclick = () => {
            const result = validateHeaders(headers, s);
            setFileStatus(key, result.match ? `✅ ${s.label} 으로 처리` : `⚠️ 헤더 불일치 (${result.ratio}%)`, result.match ? '#27ae60' : '#e74c3c');
            if (result.match) {
                fileSelections[key] = { key, file, headers, overrideKey: s.key };
                updateUploadButton();
            }
        };
        container.appendChild(btn);
    });
    statusEl.parentElement.appendChild(container);
}

function setFileStatus(key, text, color) {
    const el = document.getElementById(`file-status-${key}`);
    if (el) { el.textContent = text; el.style.color = color || '#999'; }
}

function updateUploadButton() {
    const btn = document.getElementById('btn-upload-start');
    const count = Object.keys(fileSelections).length;
    btn.disabled = count === 0 || !serverConnected;
    btn.textContent = count > 0 ? `🔄 ${count}개 파일 업데이트` : '🔄 선택한 파일 업데이트';
}

function executeUpload() {
    const keys = Object.keys(fileSelections);
    if (keys.length === 0) return;

    const progressEl = document.getElementById('upload-progress');
    const barEl = document.getElementById('upload-progress-bar');
    const statusEl = document.getElementById('upload-status-text');
    progressEl.style.display = 'block';

    let completed = 0;
    const total = keys.length;

    keys.forEach((key, idx) => {
        const sel = fileSelections[key];
        const formData = new FormData();
        formData.append('file', sel.file);
        formData.append('source_key', sel.overrideKey || key);

        statusEl.textContent = `📤 ${idx + 1}/${total}: ${UPLOAD_SOURCES.find(s => s.key === (sel.overrideKey || key)).label} 업로드중...`;

        fetch(`${SERVER_URL}/api/upload`, { method: 'POST', body: formData })
            .then(r => r.json())
            .then(data => {
                completed++;
                barEl.style.width = `${(completed / total) * 100}%`;
                if (data.success) {
                    setFileStatus(key, `✅ 업로드 완료, 파이프라인 실행중...`, '#27ae60');
                } else {
                    setFileStatus(key, `❌ 실패: ${data.error}`, '#e74c3c');
                }
                if (completed === total) {
                    statusEl.textContent = '⏳ 파이프라인 실행 완료 대기중...';
                    pollPipelineResult();
                }
            })
            .catch(err => {
                completed++;
                setFileStatus(key, `❌ 서버 오류: ${err.message}`, '#e74c3c');
                barEl.style.width = `${(completed / total) * 100}%`;
            });
    });
}

function pollPipelineResult() {
    const statusEl = document.getElementById('upload-status-text');
    let attempts = 0;
    const maxAttempts = 60;

    const check = setInterval(() => {
        attempts++;
        fetch(`${SERVER_URL}/api/pipeline-status`)
            .then(r => r.json())
            .then(data => {
                if (!data.running && data.result) {
                    clearInterval(check);
                    if (data.result.success) {
                        statusEl.innerHTML = '✅ 파이프라인 완료! <a href="#" onclick="location.reload()" style="color:#3498db;">페이지 새로고침</a>';
                        statusEl.style.color = '#27ae60';
                        document.getElementById('btn-upload-start').disabled = true;
                        document.getElementById('btn-upload-start').textContent = '✅ 업데이트 완료';
                    } else {
                        statusEl.textContent = '❌ 파이프라인 실패: ' + (data.result.error || data.result.stderr?.substring(0, 200));
                        statusEl.style.color = '#e74c3c';
                    }
                } else if (data.running) {
                    statusEl.textContent = `⏳ 파이프라인 실행중... (${attempts}초)`;
                }
                if (attempts >= maxAttempts) {
                    clearInterval(check);
                    statusEl.textContent = '⏰ 시간 초과, 서버 로그를 확인하세요 (python server.py)';
                }
            })
            .catch(() => {
                if (attempts >= maxAttempts) {
                    clearInterval(check);
                    statusEl.textContent = '⏰ 서버 연결 실패';
                }
            });
    }, 1000);
}
