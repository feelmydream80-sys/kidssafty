import csv
import json
import os

OUTPUT_DIR = 'data/originals'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process():
    results = []
    
    path = '서울특별시_동작구_횡단보도_20260306.csv'
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lat_raw = (row.get('위도', '') or '').strip()
            lng_raw = (row.get('경도', '') or '').strip()
            try:
                lat = float(lat_raw) if lat_raw else None
                lng = float(lng_raw) if lng_raw else None
            except ValueError:
                lat = None
                lng = None
            
            road_addr = (row.get('소재지도로명주소', '') or '').strip()
            jibun_addr = (row.get('소재지지번주소', '') or '').strip()
            management_id = (row.get('횡단보도관리번호', '') or '').strip()
            cw_type = (row.get('횡단보도종류', '') or '').strip()
            
            has_signal = (row.get('보행자신호등유무', '') or '').strip()
            has_audio = (row.get('음향신호기설치여부', '') or '').strip()
            has_raised = (row.get('고원식적용여부', '') or '').strip()
            bike_shared = (row.get('자전거횡단도겸용여부', '') or '').strip()
            
            lanes_raw = (row.get('차로수', '') or '').strip()
            width_raw = (row.get('횡단보도폭', '') or '').strip()
            length_raw = (row.get('횡단보도연장', '') or '').strip()
            
            try:
                lanes = float(lanes_raw) if lanes_raw else None
            except ValueError:
                lanes = None
            try:
                cw_width = float(width_raw) if width_raw else None
            except ValueError:
                cw_width = None
            try:
                cw_length = float(length_raw) if length_raw else None
            except ValueError:
                cw_length = None
            
            green_time = (row.get('녹색신호시간', '') or '').strip()
            red_time = (row.get('적색신호시간', '') or '').strip()
            
            has_island = (row.get('교통섬유무', '') or '').strip()
            has_curb_cut = (row.get('보도턱낮춤여부', '') or '').strip()
            has_blind_block = (row.get('점자블록유무', '') or '').strip()
            has_light = (row.get('집중조명시설유무', '') or '').strip()
            
            management_org = (row.get('관리기관명', '') or '').strip()
            management_phone = (row.get('관리기관전화번호', '') or '').strip()
            data_date = (row.get('데이터기준일자', '') or '').strip()
            
            record = {
                'id': f'CW-{management_id}' if management_id else f'CW-{len(results)}',
                'name': f'횡단보도({road_addr[:20]})' if road_addr else f'횡단보도-{management_id}',
                'category': 'crosswalk',
                'subcategory': '횡단보도',
                'address': road_addr or jibun_addr,
                'road_address': road_addr,
                'jibun_address': jibun_addr,
                'lat': lat,
                'lng': lng,
                'source': '횡단보도',
                'properties': {
                    'management_id': management_id,
                    'crosswalk_type': cw_type,
                    'has_signal': has_signal,
                    'has_audio_signal': has_audio,
                    'has_raised_crosswalk': has_raised,
                    'bicycle_shared': bike_shared,
                    'lanes': lanes,
                    'width': cw_width,
                    'length': cw_length,
                    'green_time': green_time,
                    'red_time': red_time,
                    'has_island': has_island,
                    'has_curb_cut': has_curb_cut,
                    'has_blind_block': has_blind_block,
                    'has_lighting': has_light,
                    'management_org': management_org,
                    'management_phone': management_phone,
                    'data_date': data_date
                }
            }
            results.append(record)
    
    output = {
        'meta': {
            'region': '동작구',
            'source': '서울특별시_동작구_횡단보도_20260306.csv',
            'total': len(results),
            'generated_at': '2026-05-13'
        },
        'items': results
    }
    
    out_path = os.path.join(OUTPUT_DIR, 'crosswalks.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'[convert_crosswalks] {len(results)}개 저장 완료: {out_path}')
    
    signal_count = sum(1 for r in results if r['properties']['has_signal'] == 'Y')
    valid_coords = sum(1 for r in results if r['lat'] is not None)
    print(f'  신호등있음: {signal_count}/{len(results)}, 유효좌표: {valid_coords}/{len(results)}')

if __name__ == '__main__':
    process()
