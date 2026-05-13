import numpy as np
import json
import os
import math
from sklearn.neighbors import KernelDensity
from data_loader import get_accidents_with_coords, get_schools_with_coords, get_crosswalks_with_coords
from utils import haversine

OUTPUT_DIR = 'data/analysis'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def collect_weighted_points():
    points = []

    accidents = get_accidents_with_coords()
    for a in accidents:
        weight = a['properties']['accident_count'] or 1
        points.append({'lat': a['lat'], 'lng': a['lng'], 'weight': weight})

    schools = get_schools_with_coords()
    for s in schools:
        points.append({'lat': s['lat'], 'lng': s['lng'], 'weight': 0.5})

    return points

def create_density_grid_from_points(points, radius_km=0.3, step=0.0015):
    lats = [p['lat'] for p in points if 'lat' in p]
    lngs = [p['lng'] for p in points if 'lng' in p]
    if not lats or not lngs:
        return []

    min_lat = min(lats) - radius_km / 111
    max_lat = max(lats) + radius_km / 111
    min_lng = min(lngs) - radius_km / (111 * math.cos(math.radians(37.5)))
    max_lng = max(lngs) + radius_km / (111 * math.cos(math.radians(37.5)))

    grid = []
    lat = min_lat
    while lat <= max_lat:
        lng = min_lng
        while lng <= max_lng:
            for p in points:
                d = haversine(lat, lng, p['lat'], p['lng'])
                if d <= radius_km * 1000:
                    grid.append({'lat': lat, 'lng': lng})
                    break
            lng += step
        lat += step

    seen = set()
    unique_grid = []
    for g in grid:
        key = (round(g['lat'], 5), round(g['lng'], 5))
        if key not in seen:
            seen.add(key)
            unique_grid.append(g)

    return unique_grid

def calculate_density(points, grid):
    if len(points) == 0:
        return []

    coords = np.array([[p['lat'], p['lng']] for p in points])
    weights = np.array([p['weight'] for p in points])

    grid_points = np.array([[g['lat'], g['lng']] for g in grid])

    kde = KernelDensity(bandwidth=0.003, kernel='gaussian')
    kde.fit(coords, sample_weight=weights)

    log_density = kde.score_samples(grid_points)
    density = np.exp(log_density)

    if density.max() > density.min():
        density_norm = (density - density.min()) / (density.max() - density.min())
    else:
        density_norm = np.zeros_like(density)

    results = []
    for i, g in enumerate(grid):
        if density_norm[i] >= 0.3:
            results.append({
                'lat': g['lat'],
                'lng': g['lng'],
                'density': round(float(density_norm[i]), 4)
            })

    return results

def main():
    print("[density_mapper] 시작...")

    points = collect_weighted_points()
    print(f"  가중치 적용 포인트: {len(points)}개")

    grid = create_density_grid_from_points(points, radius_km=0.3, step=0.0015)
    print(f"  그리드 점: {len(grid)}개")

    density_data = calculate_density(points, grid)

    if len(density_data) > 0:
        densities = [d['density'] for d in density_data]
        high = sum(1 for d in densities if d >= 0.7)
        mid = sum(1 for d in densities if 0.4 <= d < 0.7)
        low = sum(1 for d in densities if 0.3 <= d < 0.4)

        print(f"  고위험(≥0.7): {high}개")
        print(f"  중위험(0.4-0.7): {mid}개")
        print(f"  저위험(0.3-0.4): {low}개")

        output = {
            'generated_at': '2026-05-13',
            'model': 'KDE (Kernel Density Estimation)',
            'bandwidth': 0.003,
            'radius_km': 0.3,
            'total_points': len(density_data),
            'high_risk_count': high,
            'mid_risk_count': mid,
            'low_risk_count': low,
            'grid': density_data
        }

        path = os.path.join(OUTPUT_DIR, 'risk_density_grid.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"  저장 완료: {path}")
    else:
        print("  위험 밀도 포인트가 없습니다!")

if __name__ == '__main__':
    main()
