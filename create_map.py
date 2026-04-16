#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import folium
import json
import os
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE_DIR, 'output', 'unified_metadata.json'), 'r', encoding='utf-8') as f:
    metadata = json.load(f)

hotspots = metadata.get('hotspots', [])
schools = metadata.get('schools', [])

m = folium.Map(location=[35.8, 127.1], zoom_start=14, tiles='CartoDB positron')

print('[INFO] Creating 5x5m box map...')

# Accident hotspots - 5x5m RED boxes
acc_group = folium.FeatureGroup(name='Accident Hotspots', show=True)
for h in hotspots:
    if h.get('lat') and h.get('lon'):
        lat, lon = h['lat'], h['lon']
        lat_o = 5 / 111000 / 2
        lon_o = 5 / 88800 / 2
        box = [
            [lat-lat_o, lon-lon_o],
            [lat-lat_o, lon+lon_o],
            [lat+lat_o, lon+lon_o],
            [lat+lat_o, lon-lon_o],
            [lat-lat_o, lon-lon_o]
        ]
        folium.Polygon(
            locations=box,
            color='#d32f2f',
            fill=True,
            fillColor='#d32f2f',
            fillOpacity=0.7,
            weight=2,
            popup='Accident: ' + str(h.get('name', 'Unknown'))
        ).add_to(acc_group)

acc_group.add_to(m)
print('[OK] Accident zones: 4 boxes')

# Protection zones - find the file
prot_group = folium.FeatureGroup(name='Protection Zones', show=True)

# List files in data/raw
raw_dir = os.path.join(BASE_DIR, 'data/raw')
files = os.listdir(raw_dir)
print('[INFO] Files in data/raw: ' + str(files))

for filename in files:
    if '어린이' in filename:
        filepath = os.path.join(raw_dir, filename)
        print('[INFO] Loading: ' + filename)
        try:
            with open(filepath, 'r', encoding='cp949') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    try:
                        # Get lat/lon from columns
                        lat_val = None
                        lon_val = None
                        for k, v in row.items():
                            if '위도' in k:
                                lat_val = float(v)
                            if '경도' in k:
                                lon_val = float(v)
                        
                        if lat_val and lon_val and 35.7 < lat_val < 35.9 and 127.0 < lon_val < 127.2:
                            lat_o = 5 / 111000 / 2
                            lon_o = 5 / 88800 / 2
                            box = [
                                [lat_val-lat_o, lon_val-lon_o],
                                [lat_val-lat_o, lon_val+lon_o],
                                [lat_val+lat_o, lon_val+lon_o],
                                [lat_val+lat_o, lon_val-lon_o],
                                [lat_val-lat_o, lon_val-lon_o]
                            ]
                            folium.Polygon(
                                locations=box,
                                color='#1976d2',
                                fill=True,
                                fillColor='#1976d2',
                                fillOpacity=0.7,
                                weight=2
                            ).add_to(prot_group)
                            count += 1
                    except:
                        pass
                print('[OK] Protection zones: ' + str(count))
        except Exception as e:
            print('[ERROR] ' + str(e))

prot_group.add_to(m)

# Schools
school_group = folium.FeatureGroup(name='Schools', show=True)
for s in schools:
    addr = s.get('address', '')
    if addr and s.get('lat') and s.get('lon'):
        if '전주' in addr or '완주' in addr or '덕진' in addr:
            folium.Marker(
                location=[s['lat'], s['lon']],
                popup=str(s.get('name', 'School')),
                icon=folium.Icon(color='green', icon='graduation-cap', prefix='fa')
            ).add_to(school_group)
school_group.add_to(m)
print('[OK] Schools loaded')

# Legend
legend = '''
<div style="position:fixed;bottom:50px;right:50px;background:white;padding:20px;border-radius:12px;border:2px solid #333;z-index:9999;font-family:Noto Sans KR,sans-serif;">
<h4>Legend</h4>
<div style="display:flex;align-items:center;margin:10px 0;">
<div style="width:20px;height:20px;background:#d32f2f;margin-right:10px;"></div>
<div><b>Accident</b><br>5x5m</div></div>
<div style="display:flex;align-items:center;margin:10px 0;">
<div style="width:20px;height:20px;background:#1976d2;margin-right:10px;"></div>
<div><b>Protection</b><br>5x5m</div></div>
</div>
'''
m.get_root().html.add_child(folium.Element(legend))

folium.LayerControl(position='topright', collapsed=False).add_to(m)

output = os.path.join(BASE_DIR, 'output', 'risk_map.html')
m.save(output)
print('[SUCCESS] Saved: ' + output)
