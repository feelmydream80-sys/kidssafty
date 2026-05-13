import json, sys

print('===== Pipeline Verification =====\n')

# 1. locations.json 검증
print('--- 1. locations.json ---')
with open('data/locations.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data['items']
meta = data['meta']

print(f'  Total: {meta["total_items"]}')
print(f'  Valid coords: {meta["valid_coords"]}/{meta["total_items"]}')

required = ['id', 'name', 'category', 'subcategory', 'address', 'lat', 'lng', 'source', 'properties']
missing_all = 0
for item in items:
    for f in required:
        if f not in item:
            missing_all += 1
print(f'  Missing fields: {missing_all}')

has_lat = sum(1 for x in items if x['lat'] is not None)
has_lng = sum(1 for x in items if x['lng'] is not None)
print(f'  Has lat: {has_lat}, Has lng: {has_lng}')

lats = [x['lat'] for x in items if x['lat'] is not None]
lngs = [x['lng'] for x in items if x['lng'] is not None]
print(f'  Lat range: {min(lats):.4f} ~ {max(lats):.4f}')
print(f'  Lng range: {min(lngs):.4f} ~ {max(lngs):.4f}')

cats = meta['category_stats']
print(f'  Categories: {json.dumps(cats, ensure_ascii=False)}')

# 2. 각 원천 JSON 유효성 검증
print('\n--- 2. Source JSON files ---')
import os
src_dir = 'data/originals'
for fname in sorted(os.listdir(src_dir)):
    path = os.path.join(src_dir, fname)
    with open(path, 'r', encoding='utf-8') as f:
        src = json.load(f)
    meta_src = src.get('meta', {})
    print(f'  {fname}: {meta_src.get("total", 0)} items, generated={meta_src.get("generated_at","?")}')

# 3. 분석 JSON 검증
print('\n--- 3. Analysis files ---')
analysis_dir = 'data/analysis'
for fname in sorted(os.listdir(analysis_dir)):
    path = os.path.join(analysis_dir, fname)
    with open(path, 'r', encoding='utf-8') as f:
        an = json.load(f)
    print(f'  {fname}: {len(json.dumps(an))} bytes')

# 4. 이전 combined_dongjak.json과 비교
print('\n--- 4. Before/After comparison ---')
old_path = 'data/combined_dongjak.json'
with open(old_path, 'r', encoding='utf-8') as f:
    old = json.load(f)

old_schools = len(old.get('schools', []))
old_valid = sum(1 for s in old.get('schools', []) if s.get('lat') and s.get('lng'))
old_accidents = len(old.get('accident_prone_areas', []))

print(f'  [Before] schools: {old_schools} (valid coords: {old_valid})')
print(f'  [Before] accident areas: {old_accidents}')

new_schools = sum(1 for x in items if x['category'] in ['school', 'kindergarten', 'childcare', 'academy', 'special_school'])
new_schools_valid = sum(1 for x in items if x['category'] in ['school', 'kindergarten', 'childcare', 'academy', 'special_school'] and x['lat'] is not None)
new_accidents = sum(1 for x in items if x['category'] == 'accident_zone')
new_crosswalks = sum(1 for x in items if x['category'] == 'crosswalk')
new_protection = sum(1 for x in items if x['category'] == 'protection_zone')

print(f'  [After] schools/facilities: {new_schools} (valid coords: {new_schools_valid})')
print(f'  [After] accident areas: {new_accidents}')
print(f'  [After] crosswalks: {new_crosswalks}')
print(f'  [After] protection zones: {new_protection}')

# 5. 이전 안전등급과 비교
print('\n--- 5. Safety grades change ---')
old_grades_path = 'data/school_safety_grades.json'
with open(old_grades_path, 'r', encoding='utf-8') as f:
    old_grades = json.load(f)

new_grades_path = 'data/analysis/school_safety_grades.json'
with open(new_grades_path, 'r', encoding='utf-8') as f:
    new_grades = json.load(f)

print(f'  [Before] graded schools: {old_grades.get("total_schools", 0)}')
print(f'  [After] graded schools: {new_grades.get("total_schools", 0)}')

print('\n===== Verification Complete =====')
