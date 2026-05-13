# 슬라이드 1: 표지
---
**프로젝트명**: KidsSafe AI (아이 지킴이)
**부제**: 공공데이터 기반 아동 안전 PWA + AI 확장 계획
**출품분야**: AI 활용 아이디어 기획 (일반)
**제출일**: 2026년 5월
---

# 슬라이드 2: 시스템 개요 - 현재 개발된 기능
---
### KidsSafe PWA (Progressive Web App)
- **위치 추적**: GPS 기반 실시간 아이 위치 모니터링
- **위험 탐지**: 경고범위(15m) 미션발동 + 주의범위(100m) 알림표시 (범위 사용자 설정 가능)
- **알림 시스템**: 진동(모바일) + 브라우저 알림 + 미션(흔들기/회전)
- **보호자 UI**: 지도 기반 위치/위험물 표시 패널 (11종 레이어)
- **PWA**: manifest.json + Service Worker (오프라인 지원)
- **설정 커스터마이징**: 아이콘 20종 + 색상 16종 팔레트
- **데이터 업로드**: 웹 UI에서 CSV 업로드 → 자동 파이프라인 실행

### 기술 스택 (현재)
- **프론트엔드**: HTML5, CSS3, Vanilla JavaScript (ES6 Modules)
- **지도**: Leaflet.js + OpenStreetMap
- **데이터 파이프라인**: Python (CSV→JSON→분석), Flask 업로드 서버
- **알림**: Vibration API, Notification API, DeviceMotion API
- **배포**: GitHub Pages + HTTPS (PWA 필수)
- **저장**: localStorage (설정), Service Worker (오프라인 캐싱)

---

# 슬라이드 3: 활용 공공데이터 (현재 시스템)
---
| 데이터명 | 파일명 | 제공기관 | 활용 방식 |
|---------|--------|---------|------------|
| 전국교통사고다발지역표준데이터 | `https://www.data.go.kr/data/15029185/standard.do` | 한국도로교통공단 | GPS 100m 이내 탐지 |
| 전국횡단보도표준데이터 | `https://www.data.go.kr/data/15028201/standard.do#layer_data_infomation` | 서울특별시 동작구 | 횡단보도 접근 감지 |
| 학교별 위치정보 | `https://www.data.go.kr/data/15092764/fileData.do` | 교육부 | 학교 위치 표시 (실제 좌표) |
| 서울특별시 동작구_어린이보호구역 | `https://www.data.go.kr/data/15094585/fileData.do` | 서울특별시 동작구 | 어린이보호구역 + CCTV 정보 |
| 전국교통사고다발지역표준데이터 | `https://www.data.go.kr/data/15029185/standard.do` | 한국도로교통공단 | 사고다발지역 + 폴리곤 정보 |

### 데이터 파이프라인 처리
```bash
# 1. ori_data/*.csv (원천 데이터)
# 2. python convert_xxx.py → data/originals/*.json (Layer 1: CSV→JSON 변환)
# 3. python merge_locations.py → data/locations.json (Layer 2: 통합)
# 4. python risk_prediction/*.py → data/analysis/*.json (Layer 3: 분석)
# === 또는 ===
python run_pipeline.py  # 전체 10~16초 자동 실행
```

---

# 슬라이드 4: 핵심 기능 1 - GPS 추적 및 위험탐지
---
### 구현 내용 (`js/userLocation.js`)
- **GPS 추적**: `navigator.geolocation.watchPosition()` (3초 간격)
- **위험 탐지**: `checkProximity()` 함수
  ```javascript
  // 경고범위(15m): 미션 발동
  // 경고범위+3(18m): 미션 상태 유지
  // 18m+: 미션 리셋
  // 주의범위(100m): 알림 표시
  // 주의범위+3(103m): 알림 상태 유지
  // 103m+: 알림 해제
  const dist = getDistance(userLat, userLng, itemLat, itemLng);
  if (dist <= dangerR) { /* 미션 발동 */ }
  else if (dist > dangerR + 3) { /* 미션 리셋 */ }
  ```
- **설정 가능**: 경고/주의 반경 슬라이더로 자유롭게 조정
- **시각화**: 사용자 마커(📍, 최상단 레이어) + 부채꼴 위험 반경

### 지도 레이어 11종
| 레이어 | 개수 | 방식 |
|--------|------|------|
| 🟢S/M/H 학교 | 60 | 타입별 컬러 마커 |
| 🟡K 유치원 | 42 | 마커 |
| 🟠C 어린이집 | - | 마커 |
| ⚪A 학원 | 11 | 마커 |
| 🔴★ 특수학교 | 1 | 마커 |
| 🟣● 보호구역 | 61 | 원오버레이 + CCTV |
| 🔴⚠ 사고다발 | 135 | 마커 |
| ⚪· 횡단보도 | 1057 | 점 마커 |
| 🟩A~🟥F 안전등급 | 113 | 마커 |
| 🔥 위험밀도 | KDE | 히트맵 |
| 📍 사용자위치 | 1 | 최상단 마커 |

---

# 슬라이드 5: 핵심 기능 2 - 미션 시스템
---
### 미션 구현 (`js/missionSystem.js`)
- **트리거**: 횡단보도/위험지역 경고범위(15m) 진입 시 자동 발동
- **4단계 미션**:
  1. 🟢 초록불 확인 → 📱 흔들기
  2. 👀 좌우 확인 → 📱 흔들기
  3. 🔄 회전하며 살피기 → 🔄 휴대폰 회전
  4. ✅ 건너기 완료 → 📱 흔들기

### 기기 대응
- **iOS 13+**: `DeviceMotionEvent.requestPermission()` 권한 요청
- **Android**: `accelerationIncludingGravity` fallback 처리
- **데스크톱**: Enter/Space 키 또는 "스킵" 버튼으로 테스트 가능

### 진동 및 알림 (`js/alertSystem.js`)
- `navigator.vibrate([200, 100, 200])` (모바일)
- `new Notification("주의: 횡단보도 근처")` + 화면 배너

---

# 슬라이드 6: 핵심 기능 3 - 설정 UI
---
### 아이콘/색상 커스터마이징 (`js/settingsPanel.js`)
- **10개 카테고리** 각각 아이콘 20종 + 색상 16종 선택 가능
- 체크박스로 레이어 on/off
- `localStorage` 저장, 페이지 새로고침 시 유지

### 설정 메뉴 구성
```
⚙️ 설정
├── 🎨 아이콘/색상 설정 (10개 카테고리)
│   ├── 초등학교 S 🟢  중학교 M 🔵  고등학교 H 🟣
│   ├── 유치원 K 🟡  어린이집 C 🟠  학원 A ⚪
│   ├── 특수학교 ★ 🔴  보호구역 ● 🟣
│   ├── 횡단보도 · ⚪  사고다발 ⚠ 🔴
│   └─ 체크박스 → 레이어 가시성
├── 🎨 아이콘 피커 (20종)
└── 🎨 색상 팔레트 (16색)
└── 📤 데이터 업데이트 (4개 파일 업로드 슬롯)
```

### 데이터 업로드 (`server.py` + `js/dataUploader.js`)
- 4개 파일 슬롯 (학교, 보호구역, 횡단보도, 사고지역)
- CSV 선택 → 헤더 자동 검증 → 업로드 → 파이프라인 자동 실행
- 서버 미연결 시 업로드 UI 비활성화

---

# 슬라이드 7: 현재 시스템 데모 및 데이터 통합
---
### 웹 지도 통합 (`index.html` + `combined.html`)
- **11종 레이어** 지도 표시 (학교/유치원/어린이집/학원/특수학교/보호구역/사고다발/횡단보도/안전등급/히트맵/사용자)
- 보호구역: 61개소 CCTV 정보 포함 원오버레이 표시
- 히트맵: KDE 분석 기반 위험 밀도 시각화
- 범례: 레이어별 아이콘/색상 표시

### 사이드바 (테이블)
- 학교 목록 (이름, 유형, 신호등 비율)
- 사고다발지역 목록 (지점명, 사고건수, 사상자수)

### 통합 데이터 (`data/locations.json`)
- **1368개 통합 위치정보** (유효좌표 100%)
- **학교/시설 113개** (동작구, 실제 좌표)
- **사고다발지역 135개** (총 692건)
- **어린이보호구역 61개** (CCTV 정보 포함)
- **횡단보도 1057개** (신호등/차로 정보)
- **데이터 파이프라인 자동화**: `run_pipeline.py` 10초

---

# 슬라이드 8: AI 기술 도입 (실제 구현 시작)
---
### 왜 Random Forest(랜덤 포레스트)를 선택했을까요?
**💡 랜덤 포레스트란?**
- 수백 개의 **결정 트리(Decision Tree)**를 만들고, 각 트리의 예측을 투표로 모아 최종 결과를 내는 AI 방식
- 비유: **100명의 전문가에게 각각 의견을 묻고, 다수결로 결정**하는 것과 같음

**✅ 우리 시스템에 적합한 이유 (3가지)**
1. **이해하기 쉬움**: "왜 이곳이 위험한가?"를 **특징 중요도**로 설명 가능 (예: 횡단보도 밀집 35% 기여)
2. **작은 데이터에 강함**: 사고 데이터가 135개로 확장되어 안정적인 학습 가능
3. **다양한 데이터 처리**: 숫자(거리, 건수)와 범주(신호등 유무)를 동시에 잘 처리

### Random Forest로 얻은 효과
| 효과 | 설명 | 수치 |
|------|------|------|
| **높은 정확도** | 기존 사고지역 135곳 기반 학습 | 정확도 79~80% (외부 연구 수준) |
| **원인 분석** | 어떤 요인이 위험을 높이는지 파악 → "횡단보도 밀집 30% 기여" | 특징 중요도 제공 |
| **새로운 위험지역 발견** | KDE 밀도 분석 기반 고위험 구역 발굴 | 13개 고위험 구역 |
| **빠른 응답** | 새 데이터 입력 시 파이프라인 10초 완료 | 실시간 적합 |

### 실제 구현 결과
- **모델**: RandomForestRegressor (n_estimators=100)
- **학습 데이터**: 사고지역 135개 + 횡단보도 1057개 + 학교 115개 통합 활용
- **KDE 히트맵**: 13개 고위험(≥0.7), 76개 중위험(0.4~0.7), 56개 저위험(0.3~0.4)
- **저장 및 시각화**: `data/analysis/risk_density_grid.json`, `combined.html` 히트맵 표시

---

# 슬라이드 9: 데이터 분석 파이프라인
---
### 3-Layer 아키텍처
```
[Layer 1] CSV → JSON 변환 (4개 스크립트)
  ori_data/*.csv → data/originals/*.json
  - convert_schools.py (115개)
  - convert_protection_zones.py (61개, CCTV)
  - convert_crosswalks.py (1057개)
  - convert_accidents.py (135개, 692건)

[Layer 2] 통합 위치정보
  data/originals/*.json → data/locations.json (1368개)

[Layer 3] 분석 파이프라인
  data/locations.json → data/analysis/*.json
  - school_safety_grader.py (113개 안전등급)
  - accessibility_score.py (1057개 접근성)
  - signal_priority.py (722개 신호등 필요)
  - safety_index.py (113개 안전지수)
  - density_mapper.py (KDE 위험밀도)
```

### 데이터 갱신 (2가지 방법)
```bash
# 방법 1: 전체 파이프라인 (10초)
python run_pipeline.py

# 방법 2: 웹 업로드 (server.py 실행 후 index.html에서)
python server.py  # http://localhost:5000
# → ⚙️ 설정 → 데이터 업데이트 → 파일 선택 → 업로드
```

---

# 슬라이드 10: PWA 배포 및 GitHub Pages
---
### PWA 구성
- **manifest.json**: 아이콘, 테마색, standalone 모드
- **sw.js**: Service Worker - 오프라인 캐싱 + 업데이트
- **icon.svg**: 안전심볼(S) 아이콘

### GitHub Pages 배포
```
https://feelmydream80-sys.github.io/kidssafty/
```
- HTTPS → GPS/Notification API 정상 작동
- 정적 호스팅 → 서버 불필요 (지도/알림/미션 전부 동작)
- 데이터 갱신은 `git push` → Pages 자동 재배포 (2~3분)

### PWA vs file:/// 비교
| 기능 | file:/// | GitHub Pages (HTTPS) |
|------|----------|---------------------|
| ES6 import | ❌ CORS 차단 | ✅ 정상 |
| fetch(data) | ❌ 차단 | ✅ 정상 |
| GPS 위치추적 | ❌ | ✅ |
| Notification | ❌ | ✅ |
| Service Worker | ❌ | ✅ |
| 데이터 업데이트 | server.py 필요 | git push |

---

# 슬라이드 11: 시스템 확장 로드맵
---
### 개발 일정
| 단계 | 기간 | 내용 | 상태 |
|------|------|------|------|
| **1단계** | 2026.05 | PWA + 데이터 파이프라인 + 11종 지도 | ✅ 완료 |
| **2단계** | 2026.07-08 | AI 모델 고도화 (XGBoost) | 진행중 |
| **3단계** | 2026.09-10 | LSTM 이동패턴 학습 추가 | 예정 |
| **4단계** | 2026.11 | 실시간 모델 재학습 시스템 | 예정 |
| **5단계** | 2027.01~ | 전국 확대 + 모바일 앱 | 예정 |

### 현재 구현 인프라
- 통합 데이터: `data/locations.json` (1368개)
- 데이터 파이프라인: `run_pipeline.py` 10초 자동 실행
- 웹 배포: `https://feelmydream80-sys.github.io/kidssafty/`
- 설정 저장: `localStorage` (아이콘/색상/반경)

---

# 슬라이드 12: 실제 구현 성과
---
### 데이터 통합 (2026.05 기준)
✅ **5종 공공데이터 통합 → 1368개 위치정보** (유효좌표 100%)  
✅ **데이터 파이프라인 자동화**: `run_pipeline.py` 10초  
✅ **어린이보호구역 61개 신규 적용**: CCTV 정보 포함  
✅ **학교/시설 113개 실제 좌표**: 기존 7/23개 추정좌표 → 113/113 실제좌표  
✅ **사고다발지역 135개**: 총 692건 사고 데이터  

### 사용자 기능
✅ **지도 11종 레이어**: 아이콘+색상 커스터마이징  
✅ **미션 시스템**: shake/rotate, 4단계 안전교육  
✅ **PWA**: 오프라인 지원, GitHub Pages HTTPS 배포  
✅ **데이터 업로드 UI**: 웹에서 CSV 업로드 → 자동 파이프라인  

### AI 분석
✅ **학교 안전등급**: 113개 A~F (기존 7개)  
✅ **KDE 위험밀도**: 13개 고위험 구역  
✅ **신호등 우선순위**: 722개소 설치 필요 식별  

---

# 슬라이드 13: 기대 효과 및 향후 계획
---
### 기대 효과
✅ **사고 30% 감소** (AI 선제 방어 + 미션 교육)  
✅ **위험 감지 80% 단축** (5분 → 10초)  
✅ **공공데이터 활용 극대화** (5종 → 통합 분석)  
✅ **데이터 갱신 자동화** (파이프라인 10초)  

### 향후 계획
- **XGBoost 도입**: 예측 정확도 5% 향상
- **실시간 업데이트**: 새로운 사고 데이터 발생 시 파이프라인 자동 실행
- **전국 확대**: ori_data/에 새 CSV 추가 + `run_pipeline.py` 실행
- **모바일 앱**: PWA 기반 네이티브 앱 연동

---

# 슬라이드 14: 맺음말
---
### "공공데이터 + AI로 완성하는 아이 안전 지킴이"

**"우리 아이들의 안전, 지금은 PWA로, 내일은 AI로 - 오늘 바로 시작됩니다!"**

### 문의
- 프로젝트: `C:\dev\kidssafty\`
- 웹 데모: `https://feelmydream80-sys.github.io/kidssafty/`
- 통합 데이터: `data/locations.json` (1368개)
- 데이터 파이프라인: `python run_pipeline.py`
- 서버 실행: `python server.py` (데이터 업데이트 시)
