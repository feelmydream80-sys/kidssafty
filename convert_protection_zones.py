import csv
import json
import os

OUTPUT_DIR = 'data/originals'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def detect_category(facility_type):
    mapping = {
        '초등학교': ('school', '초등학교'),
        '유치원': ('kindergarten', '유치원'),
        '어린이집': ('childcare', '어린이집'),
        '특수학교': ('special_school', '특수학교'),
    }
    return mapping.get(facility_type, ('other', facility_type or '기타'))

def process():
    results = []
    
    with open('ori_data/서울특별시 동작구_어린이보호구역_20200206.csv', 'rb') as f:
        raw = f.read()
    
    for enc in ['cp949', 'euc-kr']:
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError('Cannot decode file')
    
    reader = csv.DictReader(text.splitlines())
    for row in reader:
        facility_type = (row.get('시설종류', '') or '').strip()
        name = (row.get('대상시설명', '') or '').strip()
        road_addr = (row.get('소재지도로명주소', '') or '').strip()
        jibun_addr = (row.get('소재지지번주소', '') or '').strip()
        
        lat_raw = (row.get('위도', '') or '').strip()
        lng_raw = (row.get('경도', '') or '').strip()
        try:
            lat = float(lat_raw) if lat_raw else None
            lng = float(lng_raw) if lng_raw else None
        except ValueError:
            lat = None
            lng = None
        
        cctv_yn = (row.get('카메라 설치여부(CCTV)', '') or '').strip()
        cctv_count_raw = (row.get('카메라 설치대수(CCTV)', '') or '').strip()
        try:
            cctv_count = int(cctv_count_raw) if cctv_count_raw else None
        except ValueError:
            cctv_count = None
        
        speed_limit = (row.get('보호구역제한속도', '') or '').strip()
        management = (row.get('관리기관명', '') or '').strip()
        data_date = (row.get('데이터기준일자', '') or '').strip()
        
        category, subcategory = detect_category(facility_type)
        
        rid = name.replace(' ', '')
        record = {
            'id': f'PZ-{rid}' if rid else f'PZ-{len(results)}',
            'name': name,
            'category': 'protection_zone',
            'subcategory': subcategory,
            'address': road_addr or jibun_addr,
            'road_address': road_addr,
            'jibun_address': jibun_addr,
            'lat': lat,
            'lng': lng,
            'source': '어린이보호구역',
            'properties': {
                'facility_type': facility_type,
                'cctv_yn': cctv_yn,
                'cctv_count': cctv_count,
                'speed_limit': speed_limit,
                'management': management,
                'data_date': data_date
            }
        }
        results.append(record)
    
    output = {
        'meta': {
            'region': '동작구',
            'source': '서울특별시 동작구_어린이보호구역_20200206.csv',
            'total': len(results),
            'generated_at': '2026-05-13'
        },
        'items': results
    }
    
    path = os.path.join(OUTPUT_DIR, 'protection_zones.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'[convert_protection_zones] {len(results)}개 저장 완료: {path}')
    
    cats = {}
    for r in results:
        c = r['subcategory']
        cats[c] = cats.get(c, 0) + 1
    print(f'  유형별: {cats}')
    
    cctv_count = sum(1 for r in results if r['properties']['cctv_yn'] == 'Y' or (r['properties']['cctv_count'] or 0) > 0)
    valid_coords = sum(1 for r in results if r['lat'] is not None)
    print(f'  CCTV있음: {cctv_count}/{len(results)}, 유효좌표: {valid_coords}/{len(results)}')

if __name__ == '__main__':
    process()
