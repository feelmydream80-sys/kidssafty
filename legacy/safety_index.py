import numpy as np
import json
import os
from data_loader import get_schools_with_coords, get_crosswalks_with_coords, get_accidents_with_coords
from utils import haversine

OUTPUT_DIR = 'data/analysis'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def calculate_safety_index(schools, crosswalks, accidents):
    results = []

    for school in schools:
        slat, slng = school['lat'], school['lng']

        nearby_cw = [c for c in crosswalks if haversine(slat, slng, c['lat'], c['lng']) <= 300]
        cw_score = min(len(nearby_cw) * 3, 30)

        if len(nearby_cw) > 0:
            signals = [1 if c['properties']['has_signal'] == 'Y' else 0 for c in nearby_cw]
            signal_ratio = np.mean(signals)
            signal_score = signal_ratio * 30
        else:
            signal_score = 0

        acc_near = []
        for a in accidents:
            dist = haversine(slat, slng, a['lat'], a['lng'])
            if dist <= 500:
                acc_near.append((dist, a['properties']['accident_count']))

        if len(acc_near) == 0:
            risk_score = 25
        else:
            total_accidents = sum(a[1] for a in acc_near)
            min_dist = min(a[0] for a in acc_near)
            risk_score = max(0, 25 - (total_accidents // 3) * 5 - (min_dist // 100) * 2)

        if len(nearby_cw) > 0:
            lanes_list = [c['properties']['lanes'] or 1 for c in nearby_cw]
            avg_lanes = np.mean(lanes_list)
            road_score = max(0, 15 - (avg_lanes - 1) * 3)
        else:
            road_score = 5

        total_score = cw_score + signal_score + risk_score + road_score
        total_score = min(100, max(0, total_score))

        if total_score >= 80:
            grade = '매우안전'
        elif total_score >= 60:
            grade = '안전'
        elif total_score >= 40:
            grade = '보통'
        elif total_score >= 20:
            grade = '주의'
        else:
            grade = '위험'

        results.append({
            'school_name': school['name'],
            'lat': slat,
            'lng': slng,
            'school_type': school['subcategory'],
            'total_score': round(total_score, 1),
            'grade': grade,
            'details': {
                'crosswalk_access': round(cw_score, 1),
                'signal_safety': round(signal_score, 1),
                'accident_risk': round(risk_score, 1),
                'road_safety': round(road_score, 1),
                'nearby_crosswalks': len(nearby_cw)
            }
        })

    return results

def main():
    print("[safety_index] 시작...")

    schools = get_schools_with_coords()
    crosswalks = get_crosswalks_with_coords()
    accidents = get_accidents_with_coords()
    print(f"  학교 {len(schools)}개, 횡단보도 {len(crosswalks)}개, 사고지역 {len(accidents)}개 로드")

    results = calculate_safety_index(schools, crosswalks, accidents)

    grades = {}
    for r in results:
        g = r['grade']
        grades[g] = grades.get(g, 0) + 1

    print(f"  등급 분포: {dict(sorted(grades.items()))}")

    avg_score = np.mean([r['total_score'] for r in results])
    print(f"  평균 점수: {avg_score:.1f}")

    output = {
        'generated_at': '2026-05-13',
        'total_schools': len(results),
        'average_score': round(avg_score, 1),
        'grade_distribution': grades,
        'safety_index': sorted(results, key=lambda x: x['total_score'], reverse=True)
    }

    path = os.path.join(OUTPUT_DIR, 'safety_index.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  저장 완료: {path}")

if __name__ == '__main__':
    main()
