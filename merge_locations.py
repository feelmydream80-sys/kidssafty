import json
import os

INPUT_DIR = 'data/originals'
OUTPUT = 'data/locations.json'

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def process():
    all_items = []
    source_stats = {}
    
    for fname in ['schools.json', 'protection_zones.json', 'crosswalks.json', 'accidents.json']:
        path = os.path.join(INPUT_DIR, fname)
        if not os.path.exists(path):
            print(f'  [skip] {path} not found')
            continue
        data = load_json(path)
        items = data.get('items', [])
        source = data.get('meta', {}).get('source', fname)
        source_stats[source] = len(items)
        for item in items:
            all_items.append(item)
    
    # 좌표 유효성 검증
    valid_coords = 0
    for item in all_items:
        if item['lat'] is not None and item['lng'] is not None:
            valid_coords += 1
    
    # category/type 통계
    cat_stats = {}
    for item in all_items:
        c = item['category']
        cat_stats[c] = cat_stats.get(c, 0) + 1
    
    subcat_stats = {}
    for item in all_items:
        sc = item['subcategory']
        subcat_stats[sc] = subcat_stats.get(sc, 0) + 1
    
    output = {
        'meta': {
            'region': '동작구',
            'generated_at': '2026-05-13',
            'version': '1.0',
            'total_items': len(all_items),
            'valid_coords': valid_coords,
            'source_stats': source_stats,
            'category_stats': cat_stats,
            'subcategory_stats': subcat_stats
        },
        'items': all_items
    }
    
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'[merge_locations] 통합 완료: {OUTPUT}')
    print(f'  전체: {len(all_items)}개, 유효좌표: {valid_coords}/{len(all_items)}')
    print(f'  출처별:')
    for src, cnt in source_stats.items():
        print(f'    {src}: {cnt}개')
    print(f'  카테고리별:')
    for c, cnt in sorted(cat_stats.items()):
        print(f'    {c}: {cnt}개')

if __name__ == '__main__':
    process()
