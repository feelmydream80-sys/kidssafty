from flask import Flask, request, jsonify, render_template_string, redirect, send_from_directory
import json
import math
import os
from datetime import datetime

app = Flask(__name__)

# ============== Home / Redirect ==============
@app.route('/')
def home():
    """Redirect root to admin page"""
    return redirect('/admin')

# Load metadata (경로: 실행 파일 기준으로 찾기)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, 'output', 'unified_metadata.json'), 'r', encoding='utf-8') as f:
    metadata = json.load(f)

risk_data = metadata.get('risk_data', {})
hotspots = metadata.get('hotspots', [])
schools = metadata.get('schools', [])

# ============== Admin HTML Page ==============
ADMIN_HTML = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SafeRoute AI - Admin Mode</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Malgun Gothic', sans-serif; background: #f0f2f5; padding: 20px; }
        h1 { color: #0D2137; margin-bottom: 10px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .card h2 { color: #0D2137; font-size: 18px; margin-bottom: 15px; border-bottom: 2px solid #00B4A6; padding-bottom: 10px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; font-weight: bold; margin-bottom: 5px; color: #333; }
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
        .form-group input:focus { border-color: #00B4A6; outline: none; }
        .row { display: flex; gap: 15px; }
        .row .form-group { flex: 1; }
        button { background: #00B4A6; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: bold; }
        button:hover { background: #00897B; }
        button.secondary { background: #4A6274; }
        button.danger { background: #E84545; }
        .result { background: #071828; color: #A8D5E2; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 13px; white-space: pre-wrap; max-height: 300px; overflow: auto; }
        .status { display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .status-HIGH { background: #E84545; color: white; }
        .status-MID { background: #D4860A; color: white; }
        .status-LOW { background: #1A9E5C; color: white; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #0D2137; color: white; }
        tr:hover { background: #f5f5f5; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }
        .stat-box { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-box .value { font-size: 24px; font-weight: bold; color: #0D2137; }
        .stat-box .label { font-size: 12px; color: #5A7482; }
        .tab-buttons { margin-bottom: 15px; }
        .tab-buttons button { margin-right: 10px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .preset-btn { background: #4A6274; font-size: 12px; padding: 8px 12px; margin: 3px; }
        .preset-btn:hover { background: #3d5263; }
        .preset-btn.active { background: #00B4A6; }
        .map-container { width: 100%; height: 400px; border: 1px solid #ddd; border-radius: 8px; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ SafeRoute AI - Admin Mode</h1>
        
        <div class="grid">
            <div class="stat-box">
                <div class="value">{{ stats.hotspots }}</div>
                <div class="label">사고다발지점</div>
            </div>
            <div class="stat-box">
                <div class="value">{{ stats.schools }}</div>
                <div class="label">학교</div>
            </div>
            <div class="stat-box">
                <div class="value">{{ stats.regions }}</div>
                <div class="label">위험지역</div>
            </div>
        </div>
        
        <br>
        
        <div class="tab-buttons">
            <button onclick="showTab('gps')">📍 GPS 테스트</button>
            <button onclick="showTab('time')">⏰ 시간대별 위험도</button>
            <button onclick="showTab('risk')">⚠️ 위험지역 조회</button>
            <button onclick="showTab('api')">🔌 API 테스트</button>
        </div>
        
        <!-- GPS 테스트 탭 -->
        <div id="gps" class="tab-content active">
            <div class="card">
                <h2>📍 위험 구역 편집기</h2>
                
                <!-- 편집 컨트롤 패널 -->
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <div style="margin-bottom: 10px;">
                        <strong>📐 박스 크기 선택:</strong>
                        <select id="boxSize" style="margin-left: 10px; padding: 5px;">
                            <option value="2.5">초소형 (2.5x2.5m)</option>
                            <option value="5">소형 (5x5m)</option>
                            <option value="10">중형 (10x10m)</option>
                            <option value="20">대형 (20x20m)</option>
                        </select>
                    </div>
                    <div style="margin-bottom: 10px; display: none;">
                        <strong>🎨 구역 유형:</strong>
                        <select id="zoneType" style="margin-left: 10px; padding: 5px;">
                            <option value="road">도로/횡단보도 (주황)</option>
                            <option value="accident">사고다발지역 (빨강)</option>
                            <option value="protection">어린이보호구역 (파랑)</option>
                            <option value="custom">사용자 정의 (주황)</option>
                        </select>
                    </div>
                    <div>
                        <strong>✏️ 편집 모드:</strong>
                        <button onclick="setEditMode('add')" style="background: #4CAF50; color: white; border: none; padding: 8px 15px; border-radius: 5px; margin-left: 10px; cursor: pointer;">+ 추가</button>
                        <button onclick="setEditMode('move')" style="background: #2196F3; color: white; border: none; padding: 8px 15px; border-radius: 5px; margin-left: 5px; cursor: pointer;">↔ 이동</button>
                        <button onclick="setEditMode('delete')" style="background: #f44336; color: white; border: none; padding: 8px 15px; border-radius: 5px; margin-left: 5px; cursor: pointer;">✕ 삭제</button>
                        <button onclick="setEditMode('auto')" style="background: #9C27B0; color: white; border: none; padding: 8px 15px; border-radius: 5px; margin-left: 5px; cursor: pointer;">🛣️道路上 자동</button>
                        <button onclick="setEditMode('circle')" style="background: #FF5722; color: white; border: none; padding: 8px 15px; border-radius: 5px; margin-left: 5px; cursor: pointer;">⭕ 원역자동</button>
                        <button onclick="clearAllZones()" style="background: #9E9E9E; color: white; border: none; padding: 8px 15px; border-radius: 5px; margin-left: 5px; cursor: pointer;">🗑️ 초기화</button>
                        <button onclick="goToMyLocation()" style="background: #00BCD4; color: white; border: none; padding: 8px 15px; border-radius: 5px; margin-left: 5px; cursor: pointer;">📍 내 위치</button>
                    </div>
                    <div style="margin-bottom: 10px; background: #f5f5f5; padding: 10px; border-radius: 5px;">
                        <strong>🔄 자동 생성 설정:</strong>
                        <label style="margin-left: 10px;">반경: <input type="number" id="autoRadius" value="200" style="width:60px;padding:5px;" min="10" max="500">m</label>
                        <span style="margin-left: 10px; font-size: 12px; color: #666;">(중심점 기준 선택 범위 내 도로)</span>
                    </div>
                    <div style="margin-top: 10px;">
                        <strong>💾 저장/불러오기:</strong>
                        <button onclick="saveZones()" style="background: #673AB7; color: white; border: none; padding: 8px 15px; border-radius: 5px; margin-left: 10px; cursor: pointer;">💾 저장</button>
                        <button onclick="document.getElementById('loadFile').click()" style="background: #FF9800; color: white; border: none; padding: 8px 15px; border-radius: 5px; margin-left: 5px; cursor: pointer;">📂 불러오기</button>
                        <input type="file" id="loadFile" style="display:none" onchange="loadZones(this)">
                    </div>
                    <div style="margin-top: 10px; font-size: 12px; color: #666;">
                        * 지도를 클릭해서 박스를 추가하세요. 박스를 클릭/드래그해서 이동하거나 삭제할 수 있습니다.
                    </div>
                </div>
                
                <!-- Leaflet Map Container -->
                <div id="leafletMap" class="map-container"></div>
                
                <!-- 현재 편집 모드 표시 -->
                <div id="editModeDisplay" style="margin-top: 10px; padding: 10px; background: #e3f2fd; border-radius: 5px; display: none;">
                    <strong>현재 모드:</strong> <span id="currentMode">추가</span>
                </div>
                
                <!-- Leaflet CSS & JS & Turf.js -->
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
                <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
                <script src="https://unpkg.com/@turf/turf@6/turf.min.js"></script>
                
                <script>
                    // Initialize map
                    var map = L.map('leafletMap').setView([35.8005, 127.1065], 16);
                    
                    // Add tile layer
                    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                        attribution: '&copy; OpenStreetMap & CARTO',
                        subdomains: 'abcd',
                        maxZoom: 20
                    }).addTo(map);
                    
                    // Show notification function (global)
                    function showNotification(message, isError) {
                        var notiDiv = document.createElement('div');
                        notiDiv.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:' + (isError ? '#f44336' : '#4CAF50') + ';color:white;padding:12px 24px;border-radius:8px;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-size:14px;';
                        notiDiv.innerHTML = message;
                        document.body.appendChild(notiDiv);
                        setTimeout(function() { document.body.removeChild(notiDiv); }, 3000);
                    }
                    
                    // Distance calculation function
                    function getDistanceFromLatLonInM(lat1, lon1, lat2, lon2) {
                        var R = 6371e3; // Earth's radius in meters
                        var phi1 = lat1 * Math.PI / 180;
                        var phi2 = lat2 * Math.PI / 180;
                        var dPhi = (lat2 - lat1) * Math.PI / 180;
                        var dLambda = (lon2 - lon1) * Math.PI / 180;
                        var a = Math.sin(dPhi/2) * Math.sin(dPhi/2) +
                                Math.cos(phi1) * Math.cos(phi2) *
                                Math.sin(dLambda/2) * Math.sin(dLambda/2);
                        var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                        return R * c;
                    }
                    
                    // Custom person icon
                    var personIcon = L.icon({
                        iconUrl: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzAwQjRBNiI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTAgM3MxLjY2IDAgMyAxLjM0IDMgM3MtMS4zNCAzLTMgMy0zLTEuMzQtMy0zIDEuMzQtMyAzLTN6bTAgMTQuMmMtMi41IDAtNC43MS0xLjI4LTYtMy4yMi4wMy0xLjk5IDQtMy4wOCA2LTMuMDggMiA0IDYgMS4wOSA2IDMuMDgtMS4yOSAxLjk0LTMuNSAzLjIyLTYgMy4yNnoiLz48L3N2Zz4=',
                        iconSize: [40, 40],
                        iconAnchor: [20, 40],
                        popupAnchor: [0, -40]
                    });
                    
                    // Draggable marker
                    var draggableMarker = L.marker([35.8005, 127.1065], {
                        draggable: true,
                        icon: personIcon
                    }).addTo(map);
                    
                    // Update inputs when marker is dragged
                    draggableMarker.on('dragend', function(e) {
                        var lat = e.target.getLatLng().lat.toFixed(6);
                        var lng = e.target.getLatLng().lng.toFixed(6);
                        document.getElementById('testLat').value = lat;
                        document.getElementById('testLon').value = lng;
                        
                        // Auto-check risk at new location
                        testGps();
                    });
                    
                    // Update marker when inputs change
                    function updateMarkerPosition() {
                        var lat = parseFloat(document.getElementById('testLat').value);
                        var lng = parseFloat(document.getElementById('testLon').value);
                        if (!isNaN(lat) && !isNaN(lng)) {
                            draggableMarker.setLatLng([lat, lng]);
                            map.setView([lat, lng], map.getZoom());
                        }
                    }

                    // ============== CUSTOM ZONE EDITING SYSTEM ==============
                    
                    // Zone storage
                    var customZones = [];
                    var currentEditMode = 'add'; // default to add mode (not auto)
                    var zoneLayers = {}; // Store layers by type
                    
                    // Zone colors by type
                    var zoneColors = {
                        'accident': '#d32f2f',    // Red - 사고다발지역
                        'protection': '#1976d2',  // Blue - 어린이보호구역
                        'road': '#ff5722',       // Orange - 도로/횡단보도
                        'custom': '#ff9800'       // Orange - 사용자정의
                    };
                    
                    var zoneNames = {
                        'accident': '사고다발지역',
                        'protection': '어린이보호구역',
                        'road': '도로/횡단보도',
                        'custom': '사용자정의'
                    };
                    
                    // Legend control - add to map
                    var legend = L.control({position: 'bottomright'});
                    legend.onAdd = function(map) {
                        var div = L.DomUtil.create('div', 'info legend');
                        div.style.backgroundColor = 'white';
                        div.style.padding = '10px';
                        div.style.borderRadius = '8px';
                        div.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
                        div.innerHTML = '<h4 style="margin:0 0 10px 0;"> Legend</h4>';
                        Object.keys(zoneColors).forEach(function(type) {
                            div.innerHTML += '<div style="display:flex;align-items:center;margin:5px 0;">' +
                                '<div style="width:18px;height:18px;background:' + zoneColors[type] + ';margin-right:8px;border-radius:3px;"></div>' +
                                '<span>' + zoneNames[type] + '</span></div>';
                        });
                        return div;
                    };
                    legend.addTo(map);
                    
                    // Get box size in degrees
                    function getBoxSizeMeters() {
                        var el = document.getElementById('boxSize');
                        var size = el ? (parseInt(el.value) || 2.5) : 2.5;
                        var latOffset = size / 111000;
                        return latOffset;
                    }
                    
                    // Get zone type
                    function getZoneType() {
                        var el = document.getElementById('zoneType');
                        return el ? el.value : 'road';
                    }
                    
                    // Create a box polygon
                    function createBoxCoords(lat, lon, sizeDeg) {
                        return [
                            [lat - sizeDeg/2, lon - sizeDeg/2],
                            [lat - sizeDeg/2, lon + sizeDeg/2],
                            [lat + sizeDeg/2, lon + sizeDeg/2],
                            [lat + sizeDeg/2, lon - sizeDeg/2],
                            [lat - sizeDeg/2, lon - sizeDeg/2]
                        ];
                    }
                    
                    // Set edit mode
                    function setEditMode(mode) {
                        currentEditMode = mode;
                        var modeNames = {
                            'add': '개별 추가',
                            'move': '이동',
                            'delete': '삭제',
                            'auto': '道路上 자동',
                            'circle': '원역 자동'
                        };
                        document.getElementById('currentMode').textContent = modeNames[mode] || mode;
                        document.getElementById('editModeDisplay').style.display = 'block';
                        
                        // Change cursor based on mode
                        if (mode === 'add' || mode === 'auto' || mode === 'circle') {
                            map.getContainer().style.cursor = 'crosshair';
                        } else if (mode === 'move') {
                            map.getContainer().style.cursor = 'move';
                        } else {
                            map.getContainer().style.cursor = 'not-allowed';
                        }
                    }
                    
                    // Go to my location function
                    function goToMyLocation() {
                        if (navigator.geolocation) {
                            navigator.geolocation.getCurrentPosition(function(position) {
                                var lat = position.coords.latitude;
                                var lon = position.coords.longitude;
                                map.setView([lat, lon], 17);
                                showNotification('내 위치로 이동: ' + lat.toFixed(4) + ', ' + lon.toFixed(4), false);
                            }, function(error) {
                                showNotification('위치 조회 실패: ' + error.message, true);
                            });
                        } else {
                            showNotification('브라우저가 위치 정보를 지원하지 않습니다.', true);
                        }
                    }
                    
                    // Add zone on click
                    function addZoneAtClick(e) {
                        if (currentEditMode === 'add') {
                            // Single box add
                            var lat = e.latlng.lat;
                            var lon = e.latlng.lng;
                            var sizeDeg = getBoxSizeMeters();
                            var zoneType = getZoneType();
                            
                            var zone = {
                                id: Date.now(),
                                lat: lat,
                                lon: lon,
                                size: sizeDeg,
                                type: zoneType,
                                color: zoneColors[zoneType]
                            };
                            
                            customZones.push(zone);
                            renderZone(zone);
                        } else if (currentEditMode === 'auto' || currentEditMode === 'circle') {
                            // Auto generate boxes along roads
                            generateBoxesAlongRoads(e.latlng.lat, e.latlng.lng);
                        }
                    }
                    
                    // Generate boxes along roads within radius
                    function generateBoxesAlongRoads(centerLat, centerLon) {
                        var radiusEl = document.getElementById('autoRadius');
                        var radiusM = radiusEl ? (parseInt(radiusEl.value) || 200) : 200;
                        
                        var boxSize = getBoxSizeMeters();
                        var zoneType = getZoneType();
                        var zoneColor = zoneColors[zoneType];
                        
                        // Show loading indicator
                    var loadingDiv = document.createElement('div');
                    loadingDiv.id = 'loadingDiv';
                    loadingDiv.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,0.8);color:white;padding:20px 40px;border-radius:10px;z-index:9999;font-size:16px;';
                    loadingDiv.innerHTML = '🔍 도로 조회 중...';
                    document.body.appendChild(loadingDiv);
                        
                        // Build Overpass query
                        var radiusDeg = radiusM / 111000;
                        var bbox = (centerLat - radiusDeg) + ',' + (centerLon - radiusDeg) + ',' + (centerLat + radiusDeg) + ',' + (centerLon + radiusDeg);
                        
                        var overpassUrl = 'https://overpass-api.de/api/interpreter?data=[out:json];way["highway"~"trunk|primary|secondary|tertiary|residential|service|footway"](' + bbox + ');out geom;';
                        
                        // Retry logic (up to 3 times)
                        var retries = 3;
                        function tryFetch() {
                            fetch(overpassUrl)
                                .then(function(response) { 
                                    if (!response.ok) throw new Error('Network response not ok');
                                    return response.json(); 
                                })
                                .then(function(data) {
                                    document.body.removeChild(loadingDiv);
                                    generateBoxesFromRoads(data, centerLat, centerLon, radiusM, boxSize, 'road', '#ff5722');
                                })
                                .catch(function(err) {
                                    retries--;
                                    if (retries > 0) {
                                        loadingDiv.innerHTML = '🔄 재시도 (' + retries + '회 남음)...';
                                        setTimeout(tryFetch, 2000);
                                    } else {
                                        document.body.removeChild(loadingDiv);
                                        showNotification('도로 조회 실패: ' + err.message, true);
                                    }
                                });
                        }
                        tryFetch();
                    }
                    
                    // Generate boxes from road data
                    function generateBoxesFromRoads(roadData, centerLat, centerLon, radiusM, boxSize, zoneType, zoneColor) {
                        var roadWays = roadData.elements || [];
                        var boxCount = 0;
                        var boxPolygons = [];  // Collect all boxes for merging
                        
                        var boxSizeDeg = boxSize;
                        
                        // Use user-set radius for range
                        var rangeDeg = radiusM / 111000;
                        var minLat = centerLat - rangeDeg;
                        var maxLat = centerLat + rangeDeg;
                        var minLon = centerLon - rangeDeg;
                        var maxLon = centerLon + rangeDeg;
                        
                        roadWays.forEach(function(way) {
                            if (way.geometry && way.geometry.length > 1) {
                                var nodes = way.geometry;
                                
                                for (var i = 0; i < nodes.length; i++) {
                                    var node = nodes[i];
                                    
                                    if (node.lat >= minLat && node.lat <= maxLat && 
                                        node.lon >= minLon && node.lon <= maxLon) {
                                        
                                        var boxCoords = createBoxCoords(node.lat, node.lon, boxSizeDeg);
                                        boxPolygons.push(boxCoords);
                                        boxCount++;
                                    }
                                }
                            }
                        });
                        
                        // Skip Turf.js merge - just render individual boxes directly
                        if (boxPolygons.length > 0) {
                            console.log('박스Rendering:', boxPolygons.length, '개');
                            boxPolygons.forEach(function(coords, idx) {
                                console.log('박스' + idx + ':', coords[0]);
                                var p = L.polygon(coords, {
                                    color: zoneColor,
                                    fillColor: zoneColor,
                                    fillOpacity: 0.4,
                                    weight: 2
                                }).addTo(map);
                            });
                            showNotification('총 ' + boxCount + '개 박스 생성 - 지도를 움직여 확인하세요', false);
                        } else {
                            showNotification('반경 ' + radiusM + 'm 내 도로가 없습니다.', true);
                        }
                        
                        // Also show individual boxes for debugging
                        if (boxPolygons.length > 0) {
                            var sampleBox = boxPolygons[0];
                            var boxLat = (sampleBox[0][0] + sampleBox[2][0]) / 2;
                            var boxLon = (sampleBox[0][1] + sampleBox[2][1]) / 2;
                            var dist = getDistanceFromLatLonInM(centerLat, centerLon, boxLat, boxLon);
                            console.log('생성된 박스 좌표:', sampleBox[0]);
                            console.log('중심점:', centerLat, centerLon);
                            console.log('박스 중심:', boxLat, boxLon);
                            console.log('거리:', dist.toFixed(1), 'm');
                            showNotification('박스 생성 완료 - 중심점에서 ' + dist.toFixed(0) + 'm (좌표: ' + boxLat.toFixed(4) + ', ' + boxLon.toFixed(4) + ')', false);
                        }
                    }
                    
                    // Render a zone on map
                    function renderZone(zone) {
                        var boxCoords = createBoxCoords(zone.lat, zone.lon, zone.size);
                        
                        var polygon = L.polygon(boxCoords, {
                            color: zone.color,
                            fillColor: zone.color,
                            fillOpacity: 0.4,  // 반투명
                            weight: 2,
                            opacity: 1
                        }).addTo(map);
                        
                        polygon.zoneId = zone.id;
                        
                        // Click handler
                        polygon.on('click', function(e) {
                            if (currentEditMode === 'delete') {
                                // Remove zone
                                customZones = customZones.filter(function(z) { return z.id !== zone.id; });
                                map.removeLayer(polygon);
                            } else if (currentEditMode === 'move') {
                                // Enable dragging
                                polygon.dragging.enable();
                                polygon.on('dragend', function(e) {
                                    var newLat = e.target.getLatLngs()[0][0].lat;
                                    var newLon = e.target.getLatLngs()[0][0].lng;
                                    zone.lat = newLat;
                                    zone.lon = newLon;
                                });
                            }
});
                        
                        
                }
                    
                    // Clear all custom zones
                    function clearAllZones() {
                        customZones = [];
                        // Remove all polygons from map (except tile layer)
                        map.eachLayer(function(layer) {
                            if (layer instanceof L.Polygon || layer instanceof L.CircleMarker) {
                                if (!layer._url) { // Not a tile layer
                                    map.removeLayer(layer);
                                }
                            }
                        });
                        
                        // Re-add original hotspots
                        renderHotspots();
                    }
                    
                    // Save zones to JSON
                    function saveZones() {
                        var data = JSON.stringify(customZones, null, 2);
                        var blob = new Blob([data], {type: 'application/json'});
                        var url = URL.createObjectURL(blob);
                        var a = document.createElement('a');
                        a.href = url;
                        a.download = 'risk_zones_' + Date.now() + '.json';
                        a.click();
                        URL.revokeObjectURL(url);
                    }
                    
                    // Load zones from file
                    function loadZones(input) {
                        var file = input.files[0];
                        if (!file) return;
                        
                        var reader = new FileReader();
                        reader.onload = function(e) {
                            try {
                                var zones = JSON.parse(e.target.result);
                                customZones = zones;
                                
                                // Clear current and reload
                                clearAllZones();
                                
                                zones.forEach(function(zone) {
                                    renderZone(zone);
                                });
                                
                                alert('저장된 구역 ' + zones.length + '개를 불러왔습니다.');
                            } catch (err) {
                                alert('파일 읽기 오류: ' + err.message);
                            }
                        };
                        reader.readAsText(file);
                    }
                    
                    // Render original hotspots
                    function renderHotspots() {
                        var hotspots = {{ hotspots|tojson }};
                        var boxSize = getBoxSizeMeters();
                        
                        if (hotspots) {
                            hotspots.forEach(function(h) {
                                if (h.lat && h.lon) {
                                    var lat = h.lat;
                                    var lon = h.lon;
                                    
                                    var box = createBoxCoords(lat, lon, boxSize);
                                    
                                    L.polygon(box, {
                                        color: '#d32f2f',
                                        fillColor: '#d32f2f',
                                        fillOpacity: 0.7,
                                        weight: 2
                                    }).addTo(map);
                                    
                                    L.circleMarker([lat, lon], {
                                        radius: 3,
                                        color: '#ffffff',
                                        fillColor: '#ffffff',
                                        fillOpacity: 1,
                                        weight: 1
                                    }).bindPopup('<b>' + h.name + '</b><br>사고: ' + (h.accidents || 0) + '건').addTo(map);
                                }
                            });
                        }
                    }
                    
                    // Add click handler for adding zones
                    map.on('click', addZoneAtClick);
                    
                    // Initialize - auto load roads on current view
                    map.whenReady(function() {
                        var center = map.getCenter();
                        var radiusEl = document.getElementById('autoRadius');
                        var radiusM = radiusEl ? (parseInt(radiusEl.value) || 200) : 200;
                        var boxSize = getBoxSizeMeters();
                        
                        // Auto generate on initial load
                        generateBoxesAlongRoads(center.lat, center.lng);
                    });
                    
                    // Initialize - render hotspots
                    renderHotspots();
                </script>
                
                <div class="form-group">
                    <label>위도 (Latitude)</label>
                    <input type="number" id="testLat" step="0.0001" value="35.8" placeholder="예: 35.8" onchange="updateMarkerPosition()">
                </div>
                <div class="form-group">
                    <label>경도 (Longitude)</label>
                    <input type="number" id="testLon" step="0.0001" value="127.1" placeholder="예: 127.1" onchange="updateMarkerPosition()">
                </div>
                <div class="form-group">
                    <label>시간 (hour)</label>
                    <input type="number" id="testHour" min="0" max="23" value="8">
                </div>
                <div class="form-group">
                    <label>프리셋 위치</label>
                    <div>
                        <button class="preset-btn" onclick="setPreset('전주효천초')">전주효천초 부근</button>
                        <button class="preset-btn" onclick="setPreset('전주완산초')">전주완산초 부근</button>
                        <button class="preset-btn" onclick="setPreset('금평동')">금평동 (고위험)</button>
                        <button class="preset-btn" onclick="setPreset('중화동')">중화동 (고위험)</button>
                        <button class="preset-btn" onclick="setPreset('효자동')">효자동</button>
                    </div>
                </div>
                <button onclick="testGps()">🔍 위험도 조회</button>
                <button class="secondary" onclick="randomLocation()">🎲 랜덤 위치</button>
            </div>
            
            <div class="card" id="gpsResult" style="display:none">
                <h2>📊 결과</h2>
                <div id="gpsResultContent" class="result"></div>
            </div>
        </div>
        
        <!-- 시간대별 위험도 탭 -->
        <div id="time" class="tab-content">
            <div class="card">
                <h2>⏰ 시간대별 위험도 분석</h2>
                <div class="form-group">
                    <label>지역 선택</label>
                    <select id="timeRegion">
                        <option value="">전체</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>시간 범위</label>
                    <div>
                        <button class="preset-btn" onclick="setTimeRange('all')">전체 (0-23시)</button>
                        <button class="preset-btn" onclick="setTimeRange('school')">통학 시간 (7-17시)</button>
                        <button class="preset-btn" onclick="setTimeRange('morning')">등교 시간 (7-9시)</button>
                        <button class="preset-btn" onclick="setTimeRange('afternoon')">하교 시간 (12-17시)</button>
                    </div>
                </div>
                <button onclick="analyzeTimeRisk()">📈 분석</button>
            </div>
            
            <div class="card" id="timeResult" style="display:none">
                <h2>📊 시간대별 위험도</h2>
                <div id="timeResultContent"></div>
            </div>
        </div>
        
        <!-- 위험지역 조회 탭 -->
        <div id="risk" class="tab-content">
            <div class="card">
                <h2>⚠️ 위험지역 목록</h2>
                <button onclick="loadRiskAreas()">🔄 목록 불러오기</button>
            </div>
            
            <div class="card" id="riskList" style="display:none">
                <table id="riskTable">
                    <thead>
                        <tr>
                            <th>순위</th>
                            <th>지역</th>
                            <th>총사고</th>
                            <th>통학시간사고</th>
                            <th>위험시간대</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
        
        <!-- API 테스트 탭 -->
        <div id="api" class="tab-content">
            <div class="card">
                <h2>🔌 API 직접 호출 테스트</h2>
                <div class="form-group">
                    <label>엔드포인트</label>
                    <select id="apiEndpoint">
                        <option value="/api/metadata">/api/metadata</option>
                        <option value="/api/hotspots">/api/hotspots</option>
                        <option value="/api/schools">/api/schools</option>
                        <option value="/api/risk?lat=35.8&lon=127.1&hour=8">/api/risk (전주, 8시)</option>
                        <option value="/api/zones?lat=35.8&lon=127.1&radius=500">/api/zones (반경 500m)</option>
                    </select>
                </div>
                <button onclick="testApi()">🚀 호출</button>
            </div>
            
            <div class="card" id="apiResult" style="display:none">
                <h2>📄 응답</h2>
                <div id="apiResultContent" class="result"></div>
            </div>
        </div>
    </div>
    
    <script>
        // Preset locations
        const presets = {
            '전주효천초': { lat: 35.8000, lon: 127.1034 },
            '전주완산초': { lat: 35.7968, lon: 127.0850 },
            '금평동': { lat: 35.8290, lon: 127.0450 },
            '중화동': { lat: 35.8200, lon: 127.0400 },
            '효자동': { lat: 35.7900, lon: 127.1000 }
        };
        
        function setPreset(name) {
            console.log('Setting preset:', name);
            const p = presets[name];
            if (p) {
                document.getElementById('testLat').value = p.lat;
                document.getElementById('testLon').value = p.lon;
                console.log('Preset applied:', p);
            } else {
                console.error('Preset not found:', name);
            }
        }
        
        function randomLocation() {
            // Random location in Jeonju area
            const lat = 35.75 + Math.random() * 0.15;
            const lon = 127.0 + Math.random() * 0.2;
            document.getElementById('testLat').value = lat.toFixed(4);
            document.getElementById('testLon').value = lon.toFixed(4);
        }
        
        async function testGps() {
            const lat = document.getElementById('testLat').value;
            const lon = document.getElementById('testLon').value;
            const hour = document.getElementById('testHour').value;
            
            const url = `/api/risk?lat=${lat}&lon=${lon}&hour=${hour}`;
            
            try {
                const res = await fetch(url);
                const data = await res.json();
                
                document.getElementById('gpsResult').style.display = 'block';
                document.getElementById('gpsResultContent').textContent = JSON.stringify(data, null, 2);
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }
        
        async function analyzeTimeRisk() {
            const region = document.getElementById('timeRegion').value;
            const url = region ? `/api/risk/${region}` : `/api/risk?lat=35.8&lon=127.1&hour=8`;
            
            try {
                const res = await fetch('/api/metadata');
                const meta = await res.json();
                
                document.getElementById('timeResult').style.display = 'block';
                
                let html = '<table><tr><th>시간</th><th>사고건수</th><th>위험점수</th><th>등급</th></tr>';
                
                // Show sample for demonstration
                const hours = ['07', '08', '09', '12', '14', '16', '17'];
                hours.forEach(h => {
                    html += `<tr>
                        <td>${h}시</td>
                        <td>${Math.floor(Math.random() * 30) + 10}</td>
                        <td>${(Math.random() * 0.15).toFixed(3)}</td>
                        <td><span class="status ${Math.random() > 0.5 ? 'HIGH' : 'MID'}">${Math.random() > 0.5 ? 'HIGH' : 'MID'}</span></td>
                    </tr>`;
                });
                html += '</table>';
                
                document.getElementById('timeResultContent').innerHTML = html;
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }
        
        async function loadRiskAreas() {
            const url = '/api/metadata';
            
            try {
                const res = await fetch(url);
                const data = await res.json();
                
                document.getElementById('riskList').style.display = 'block';
                
                // Sample high risk areas
                const areas = [
                    ['금평동', 226, 98],
                    ['중화동1가', 201, 87],
                    ['필삼동', 190, 82],
                    ['봉황동2동', 176, 76],
                    ['삼천동', 165, 71]
                ];
                
                let html = '';
                areas.forEach((a, i) => {
                    html += `<tr>
                        <td>${i+1}</td>
                        <td>${a[0]}</td>
                        <td>${a[1]}</td>
                        <td>${a[2]}</td>
                        <td><span class="status-HIGH">HIGH</span></td>
                    </tr>`;
                });
                
                document.querySelector('#riskTable tbody').innerHTML = html;
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }
        
        async function testApi() {
            const endpoint = document.getElementById('apiEndpoint').value;
            
            try {
                const res = await fetch(endpoint);
                const data = await res.json();
                
                document.getElementById('apiResult').style.display = 'block';
                document.getElementById('apiResultContent').textContent = JSON.stringify(data, null, 2);
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }
        
        function showTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
        }
        
        // Load regions on init
        async function init() {
            try {
                const res = await fetch('/api/metadata');
                const data = await res.json();
                
                // Populate region select
                const select = document.getElementById('timeRegion');
                select.innerHTML = '<option value="">전체</option>';
                
                if (data.risk_data) {
                    Object.keys(data.risk_data).sort().forEach(region => {
                        const option = document.createElement('option');
                        option.value = region;
                        option.textContent = region;
                        select.appendChild(option);
                    });
                }
            } catch(e) {
                console.error('Failed to load regions:', e);
            }
        }
        
        // Track active time range button
        function setTimeRange(range) {
            // Remove active class from all time range buttons
            document.querySelectorAll('#time .preset-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Add active class to clicked button (find by onclick attribute)
            const buttons = document.querySelectorAll('#time .preset-btn');
            buttons.forEach(btn => {
                if (btn.getAttribute('onclick').includes(`'${range}'`)) {
                    btn.classList.add('active');
                }
            });
            
            // Update time input based on range
            if (range === 'school') {
                document.getElementById('testHour').value = 8;
            } else if (range === 'morning') {
                document.getElementById('testHour').value = 8;
            } else if (range === 'afternoon') {
                document.getElementById('testHour').value = 14;
            } else if (range === 'all') {
                document.getElementById('testHour').value = 12;
            }
        }
        init();
    </script>
</body>
</html>
'''

# ============== Utility Functions ==============
def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters"""
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon/2)**2)
    return R * 2 * math.asin(math.sqrt(a))

def get_risk_level(region, hour):
    """Get risk level for specific region and hour"""
    if region not in risk_data:
        return {"grade": "LOW", "score": 0.0, "count": 0}
    
    region_data = risk_data[region]
    hour_str = str(hour).zfill(2)
    
    if hour_str in region_data.get('risk_by_hour', {}):
        return region_data['risk_by_hour'][hour_str]
    
    return {"grade": "LOW", "score": 0.0, "count": 0}

def is_school_time(hour):
    """Check if it's school commute time (07-09, 12-17)"""
    return (7 <= hour <= 9) or (12 <= hour <= 17)

# ============== API Endpoints ==============

@app.route('/api/risk', methods=['GET'])
def get_risk():
    """
    Get risk level for location and time
    Parameters: lat, lon, hour (optional)
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    hour = request.args.get('hour', default=datetime.now().hour, type=int)
    
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon required"}), 400
    
    # Find nearest hotspot
    nearest_hotspot = None
    min_dist = float('inf')
    
    for h in hotspots:
        if h.get('lat') and h.get('lon'):
            dist = haversine(lat, lon, h['lat'], h['lon'])
            if dist < min_dist:
                min_dist = dist
                nearest_hotspot = h
    
    # Determine if alert should trigger
    alert_triggered = False
    if nearest_hotspot and min_dist <= 300:  # Within 300m
        if is_school_time(hour):
            # Need region info - use nearest school as proxy
            alert_triggered = True
    
    return jsonify({
        "lat": lat,
        "lon": lon,
        "hour": hour,
        "is_school_time": is_school_time(hour),
        "nearest_hotspot": nearest_hotspot['name'] if nearest_hotspot else None,
        "distance_m": round(min_dist) if nearest_hotspot else None,
        "alert_triggered": alert_triggered
    })

@app.route('/api/risk/<region>', methods=['GET'])
def get_region_risk(region):
    """
    Get risk data for specific region
    """
    hour = request.args.get('hour', default=datetime.now().hour, type=int)
    
    risk = get_risk_level(region, hour)
    
    return jsonify({
        "region": region,
        "hour": hour,
        "risk": risk
    })

@app.route('/api/zones', methods=['GET'])
def get_zones():
    """
    Get protection zones within radius
    Parameters: lat, lon, radius (meters, default 500)
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', default=500, type=float)
    
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon required"}), 400
    
    nearby_zones = []
    for h in hotspots:
        if h.get('lat') and h.get('lon'):
            dist = haversine(lat, lon, h['lat'], h['lon'])
            if dist <= radius:
                nearby_zones.append({
                    "name": h['name'],
                    "lat": h['lat'],
                    "lon": h['lon'],
                    "accidents": h.get('accidents', 0),
                    "distance_m": round(dist)
                })
    
    return jsonify({
        "center": {"lat": lat, "lon": lon},
        "radius": radius,
        "zones": nearby_zones,
        "count": len(nearby_zones)
    })

@app.route('/api/hotspots', methods=['GET'])
def get_hotspots():
    """
    Get all hotspot data
    """
    return jsonify({
        "hotspots": hotspots,
        "count": len(hotspots)
    })

@app.route('/api/schools', methods=['GET'])
def get_schools():
    """
    Get school data with optional filtering
    Parameters: region (optional), type (optional)
    """
    region = request.args.get('region')
    school_type = request.args.get('type')
    
    filtered_schools = schools
    
    if region:
        filtered_schools = [s for s in filtered_schools if region in s.get('district', '')]
    if school_type:
        filtered_schools = [s for s in filtered_schools if school_type in s.get('type', '')]
    
    return jsonify({
        "schools": filtered_schools[:100],  # Limit to 100
        "count": len(filtered_schools)
    })

@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    """
    Get metadata summary
    """
    return jsonify(metadata['metadata'])

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/admin', methods=['GET'])
def admin_page():
    """Admin mode web interface"""
    stats = metadata.get('metadata', {}).get('stats', {})
    return render_template_string(ADMIN_HTML, 
        stats={
            'hotspots': stats.get('total_hotspots', 0),
            'schools': stats.get('total_schools', 0),
            'regions': stats.get('total_regions', 0)
        },
        hotspots=hotspots
    )

@app.route('/output/<path:filename>')
def serve_output(filename):
    """Serve files from output directory"""
    return send_from_directory(os.path.join(BASE_DIR, 'output'), filename)

# ============== Main ==============
if __name__ == '__main__':
    print("=" * 50)
    print("SafeRoute AI API Server")
    print("=" * 50)
    print(f"Loaded: {metadata['metadata']['stats']}")
    print("\nEndpoints:")
    print("  GET /api/risk?lat=&lon=&hour=   - Get risk for location")
    print("  GET /api/risk/<region>          - Get risk for region")
    print("  GET /api/zones?lat=&lon=&radius= - Get nearby zones")
    print("  GET /api/hotspots               - Get all hotspots")
    print("  GET /api/schools                - Get schools")
    print("  GET /api/metadata               - Get metadata")
    print("\nRunning on http://localhost:5000")
    app.run(port=5000, debug=True)