"""
[DEPRECATED] 이 스크립트는 이제 사용하지 않습니다.
대신 run_pipeline.py를 통해 전체 파이프라인을 실행하세요.

변경 사항:
- convert_schools.py: 학교별위치정보 CSV → JSON (정확한 좌표)
- convert_protection_zones.py: 어린이보호구역 CSV → JSON
- convert_crosswalks.py: 횡단보도 CSV → JSON
- convert_accidents.py: 사고다발지역 CSV → JSON
- merge_locations.py: 통합 locations.json 생성
"""

import re
import csv
import json
import io

# 1. m.md 파싱 (HTML SlickGrid)
with open('m.md', 'r', encoding='utf-8') as f:
    html = f.read()

# 정규식으로 각 row의 cell 텍스트 추출
cell_pattern = r'<div class="slick-cell[^>]*>(.*?)</div>'
cells = re.findall(cell_pattern, html, re.DOTALL)
schools = []
for i in range(0, len(cells), 5):
    chunk = cells[i:i+5]
    if len(chunk) == 5:
        name = re.sub(r'<[^>]+>', '', chunk[0]).strip()
        type_ = re.sub(r'<[^>]+>', '', chunk[1]).strip()
        date_str = re.sub(r'<[^>]+>', '', chunk[2]).strip()
        address = re.sub(r'<[^>]+>', '', chunk[3]).strip()
        value = re.sub(r'<[^>]+>', '', chunk[4]).strip()
        date_match = re.match(r'(\d{4})년 (\d{2})월 (\d{2})일', date_str)
        if date_match:
            established = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
        else:
            established = date_str
        schools.append({
            "name": name,
            "type": type_,
            "established": established,
            "address": address,
            "accident_count": int(value) if value.isdigit() else 0
        })

# 2. child_safety_zones.csv 에서 동작구 데이터 추출 및 동별 좌표 매핑
accident_areas = []
dong_coords = {}  # 동 이름 -> 좌표 리스트
with open('data/child_safety_zones.csv', 'r', encoding='utf-8') as f:
    content = f.read()
    if content.startswith('\ufeff'):
        content = content[1:]
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        if '동작구' in row.get('시도시군구명', ''):
            lat = float(row.get('위도', 0))
            lng = float(row.get('경도', 0))
            location = row.get('지점명', '')
            # 지점명에서 동 이름 추출 (예: "동작구 상도동(상도동다빈모1프라자 부근)" -> "상도동")
            dong_match = re.search(r'동작구\s+(\S+동)', location)
            if dong_match:
                dong = dong_match.group(1)
                if dong not in dong_coords:
                    dong_coords[dong] = []
                dong_coords[dong].append((lat, lng))
            accident_areas.append({
                "fid": row.get('사고다발지fid', ''),
                "id": row.get('사고다발지id', ''),
                "region": row.get('시도시군구명', ''),
                "location": location,
                "accidents": int(row.get('사고건수', 0)),
                "casualties": int(row.get('사상자수', 0)),
                "deaths": int(row.get('사망자수', 0)),
                "lng": lng,
                "lat": lat
            })

# 3. 학교 주소에서 동 추출하고 좌표 할당
def extract_dong(address):
    # 괄호 안의 동 이름 추출 (예: (흑석동))
    paren_match = re.search(r'\((\S+동)\)', address)
    if paren_match:
        return paren_match.group(1)
    # 괄호 없으면 주소 끝부분의 동 추출
    matches = re.findall(r'(\S+동)', address)
    if matches:
        return matches[-1]  # 마지막 동 이름
    return None

for school in schools:
    address = school['address']
    dong = extract_dong(address)
    if dong and dong in dong_coords and dong_coords[dong]:
        # 해당 동의 첫 번째 좌표 사용
        coords = dong_coords[dong][0]
        school['lat'] = coords[0]
        school['lng'] = coords[1]
    else:
        school['lat'] = None
        school['lng'] = None

# 4. 통합 JSON 생성
combined = {
    "region": "동작구",
    "schools": schools,
    "accident_prone_areas": accident_areas
}

with open('data/combined_dongjak.json', 'w', encoding='utf-8') as f:
    json.dump(combined, f, ensure_ascii=False, indent=2)

print(f"학교 {len(schools)}개, 사고다발지역 {len(accident_areas)}개 통합 완료")
print("저장: data/combined_dongjak.json")
