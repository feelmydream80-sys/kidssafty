import csv
import json
import os
import re

OUTPUT_DIR = 'data/originals'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_polygon(text):
    if not text:
        return None
    try:
        text_clean = text.strip()
        if text_clean.startswith('"') and text_clean.endswith('"'):
            text_clean = text_clean[1:-1]
        text_clean = text_clean.replace('""', '"')
        parsed = json.loads(text_clean)
        if isinstance(parsed, dict) and 'coordinates' in parsed:
            return parsed
        return None
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        coord_match = re.findall(r'\[([\d\.\-]+),\s*([\d\.\-]+)\]', text)
        if coord_match and len(coord_match) > 3:
            coords = [[float(x), float(y)] for x, y in coord_match]
            return {'type': 'Polygon', 'coordinates': [coords]}
    except (ValueError, TypeError):
        pass
    return None

def process():
    results = []
    
    with open('ori_data/전국교통사고다발지역표준데이터.csv', 'rb') as f:
        raw = f.read()
    
    for enc in ['cp949', 'euc-kr']:
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError('Cannot decode file')
    
    if text.startswith('\ufeff'):
        text = text[1:]
    
    reader = csv.DictReader(text.splitlines())
    for row in reader:
        sido = (row.get('사고다발지역시도시군구', '') or '').strip()
        if '동작구' not in sido:
            continue
        
        name = (row.get('사고지역위치명', '') or '').strip()
        
        lat_raw = (row.get('위도', '') or '').strip()
        lng_raw = (row.get('경도', '') or '').strip()
        try:
            lat = float(lat_raw) if lat_raw else None
            lng = float(lng_raw) if lng_raw else None
        except ValueError:
            lat = None
            lng = None
        
        accidents_raw = (row.get('사고건수', '') or '').strip()
        casualties_raw = (row.get('사상자수', '') or '').strip()
        deaths_raw = (row.get('사망자수', '') or '').strip()
        serious_raw = (row.get('중상자수', '') or '').strip()
        minor_raw = (row.get('경상자수', '') or '').strip()
        report_raw = (row.get('부상신고자수', '') or '').strip()
        
        try:
            accidents = int(accidents_raw) if accidents_raw else 0
        except ValueError:
            accidents = 0
        try:
            casualties = int(casualties_raw) if casualties_raw else 0
        except ValueError:
            casualties = 0
        try:
            deaths = int(deaths_raw) if deaths_raw else 0
        except ValueError:
            deaths = 0
        try:
            serious = int(serious_raw) if serious_raw else 0
        except ValueError:
            serious = 0
        try:
            minor = int(minor_raw) if minor_raw else 0
        except ValueError:
            minor = 0
        try:
            report = int(report_raw) if report_raw else 0
        except ValueError:
            report = 0
        
        rid = (row.get('사고다발지역관리번호', '') or '').strip()
        year = (row.get('사고연도', '') or '').strip()
        loc_code = (row.get('위치코드', '') or '').strip()
        road_addr = (row.get('사고지역위치명', '') or '').strip()
        polygon_raw = (row.get('사고다발지역폴리곤정보', '') or '').strip()
        polygon = extract_polygon(polygon_raw)
        
        record = {
            'id': f'AZ-{rid}' if rid else f'AZ-{len(results)}',
            'name': name,
            'category': 'accident_zone',
            'subcategory': '사고다발지역',
            'address': road_addr or name,
            'road_address': road_addr,
            'lat': lat,
            'lng': lng,
            'source': '전국교통사고다발지역표준데이터',
            'properties': {
                'management_id': rid,
                'year': year,
                'location_code': loc_code,
                'accident_count': accidents,
                'casualties': casualties,
                'deaths': deaths,
                'serious_injuries': serious,
                'minor_injuries': minor,
                'report_injuries': report,
                'polygon': polygon
            }
        }
        results.append(record)
    
    output = {
        'meta': {
            'region': '동작구',
            'source': '전국교통사고다발지역표준데이터.csv',
            'total': len(results),
            'generated_at': '2026-05-13'
        },
        'items': results
    }
    
    out_path = os.path.join(OUTPUT_DIR, 'accidents.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'[convert_accidents] {len(results)}개 저장 완료: {out_path}')
    
    total_acc = sum(r['properties']['accident_count'] for r in results)
    total_deaths = sum(r['properties']['deaths'] for r in results)
    valid_coords = sum(1 for r in results if r['lat'] is not None)
    print(f'  총사고건수: {total_acc}, 사망자수: {total_deaths}, 유효좌표: {valid_coords}/{len(results)}')

if __name__ == '__main__':
    process()
