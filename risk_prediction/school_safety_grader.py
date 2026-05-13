import numpy as np
import json
import os
from data_loader import get_schools_with_coords, get_crosswalks_with_coords
from utils import haversine

OUTPUT_DIR = 'data/analysis'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def calculate_school_features(schools, crosswalks):
    results = []

    for school in schools:
        slat, slng = school['lat'], school['lng']

        nearby = [c for c in crosswalks if haversine(slat, slng, c['lat'], c['lng']) <= 300]

        if len(nearby) == 0:
            features = {
                'school_name': school['name'],
                'lat': slat,
                'lng': slng,
                'crosswalk_count': 0,
                'signal_ratio': 0,
                'avg_lanes': 1,
                'min_distance': 500,
                'safety_grade': 'F'
            }
        else:
            signals = [1 if c['properties']['has_signal'] == 'Y' else 0 for c in nearby]
            signal_ratio = np.mean(signals)
            lanes_list = [c['properties']['lanes'] or 1 for c in nearby]
            avg_lanes = np.mean(lanes_list)
            distances = [haversine(slat, slng, c['lat'], c['lng']) for c in nearby]
            min_dist = min(distances)

            score = 0
            score += len(nearby) * 10
            score += signal_ratio * 30
            score -= (min_dist / 50) * 5
            score -= (avg_lanes - 1) * 3

            if score >= 40:
                grade = 'A'
            elif score >= 30:
                grade = 'B'
            elif score >= 20:
                grade = 'C'
            elif score >= 10:
                grade = 'D'
            else:
                grade = 'F'

            features = {
                'school_name': school['name'],
                'lat': slat,
                'lng': slng,
                'crosswalk_count': len(nearby),
                'signal_ratio': round(signal_ratio, 2),
                'avg_lanes': round(avg_lanes, 1),
                'min_distance': round(min_dist, 1),
                'safety_score': round(score, 1),
                'safety_grade': grade
            }

        results.append(features)

    return results

def main():
    print("[school_safety_grader] 시작...")

    schools = get_schools_with_coords()
    crosswalks = get_crosswalks_with_coords()
    print(f"  학교 {len(schools)}개, 횡단보도 {len(crosswalks)}개 로드")

    results = calculate_school_features(schools, crosswalks)

    output = {
        'generated_at': '2026-05-13',
        'total_schools': len(results),
        'safety_grades': results
    }

    path = os.path.join(OUTPUT_DIR, 'school_safety_grades.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    grades = {}
    for r in results:
        g = r['safety_grade']
        grades[g] = grades.get(g, 0) + 1

    print(f"  등급 분포: {dict(sorted(grades.items()))}")
    print(f"  저장 완료: {path}")

if __name__ == '__main__':
    main()
