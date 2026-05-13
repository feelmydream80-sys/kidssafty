import csv
import json
import sys
import os

OUTPUT_DIR = 'data/originals'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def detect_category(name, addr):
    name = name or ''
    addr = addr or ''
    combined = name + addr
    if '초등학교' in combined:
        return ('school', '초등학교')
    elif '중학교' in combined:
        return ('school', '중학교')
    elif '고등학교' in combined:
        return ('school', '고등학교')
    elif '유치원' in combined:
        if '병설' in combined:
            return ('kindergarten', '유치원(병설)')
        return ('kindergarten', '유치원(일반)')
    elif '어린이집' in combined:
        return ('childcare', '어린이집')
    elif '학원' in combined:
        return ('academy', '학원')
    elif '특수학교' in combined or '특수' in combined:
        return ('special_school', '특수학교')
    elif '대학교' in combined or '대학' in combined:
        return ('university', '대학교')
    elif '외국인학교' in combined or '외국' in combined:
        return ('international_school', '외국인학교')
    elif '국제' in combined:
        return ('international_school', '국제학교')
    else:
        return ('other', '기타')

def process():
    results = []
    seen = set()
    
    with open('ori_data/학교별위치정보_202412270000001.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            road_addr = (row.get('학교도로명주소', '') or '').strip()
            old_addr = (row.get('학교주소', '') or '').strip()
            detail_addr = (row.get('학교도로명상세주소', '') or '').strip()
            full_addr = road_addr or old_addr
            
            if '동작구' not in full_addr:
                continue
            
            name = (row.get('학교코드명', '') or '').strip()
            if not name:
                continue
            if name in seen:
                continue
            seen.add(name)
            
            lat_raw = (row.get('위도값', '') or '').strip()
            lng_raw = (row.get('경도값', '') or '').strip()
            try:
                lat = float(lat_raw) if lat_raw else None
                lng = float(lng_raw) if lng_raw else None
            except ValueError:
                lat = None
                lng = None
            
            code = (row.get('학교코드', '') or '').strip()
            postal = (row.get('우편번호', '') or '').strip()
            
            category, subcategory = detect_category(name, detail_addr + full_addr)
            
            record = {
                'id': f'SCH-{code}' if code else f'SCH-{name}',
                'name': name,
                'category': category,
                'subcategory': subcategory,
                'address': full_addr,
                'road_address': road_addr,
                'detail_address': detail_addr,
                'lat': lat,
                'lng': lng,
                'source': '학교별위치정보',
                'properties': {
                    'school_code': code,
                    'postal_code': postal
                }
            }
            results.append(record)
    
    output = {
        'meta': {
            'region': '동작구',
            'source': '학교별위치정보_202412270000001.csv',
            'total': len(results),
            'generated_at': '2026-05-13'
        },
        'items': results
    }
    
    path = os.path.join(OUTPUT_DIR, 'schools.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'[convert_schools] {len(results)}개 저장 완료: {path}')
    
    cats = {}
    for r in results:
        c = r['subcategory']
        cats[c] = cats.get(c, 0) + 1
    print(f'  유형별: {cats}')
    
    valid_coords = sum(1 for r in results if r['lat'] is not None)
    print(f'  유효좌표: {valid_coords}/{len(results)}')

if __name__ == '__main__':
    process()
