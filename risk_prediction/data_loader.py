import json

LOCATIONS_PATH = 'data/locations.json'

_locations_cache = None

def load_locations():
    global _locations_cache
    if _locations_cache is not None:
        return _locations_cache
    with open(LOCATIONS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _locations_cache = data['items']
    return _locations_cache

def filter_by_category(category):
    items = load_locations()
    return [x for x in items if x['category'] == category]

def filter_by_categories(categories):
    items = load_locations()
    return [x for x in items if x['category'] in categories]

def get_schools():
    return filter_by_categories(['school', 'kindergarten', 'childcare', 'academy',
                                  'special_school', 'university', 'international_school'])

def get_schools_with_coords():
    return [s for s in get_schools() if s['lat'] is not None and s['lng'] is not None]

def get_crosswalks():
    return filter_by_category('crosswalk')

def get_crosswalks_with_coords():
    return [c for c in get_crosswalks() if c['lat'] is not None and c['lng'] is not None]

def get_accidents():
    return filter_by_category('accident_zone')

def get_accidents_with_coords():
    return [a for a in get_accidents() if a['lat'] is not None and a['lng'] is not None]

def get_protection_zones():
    return filter_by_category('protection_zone')

def get_protection_zones_with_coords():
    return [p for p in get_protection_zones() if p['lat'] is not None and p['lng'] is not None]

def create_grid(min_lat=37.48, max_lat=37.52, min_lng=126.90, max_lng=126.95, step=0.001):
    grid_points = []
    lat = min_lat
    while lat <= max_lat:
        lng = min_lng
        while lng <= max_lng:
            grid_points.append({'lat': lat, 'lng': lng})
            lng += step
        lat += step
    return grid_points

def get_stats():
    items = load_locations()
    cats = {}
    for item in items:
        c = item['category']
        cats[c] = cats.get(c, 0) + 1
    return {
        'total': len(items),
        'categories': cats
    }
