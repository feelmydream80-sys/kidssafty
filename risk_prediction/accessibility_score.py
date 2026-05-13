import numpy as np
import json
import os
from data_loader import get_schools_with_coords, get_crosswalks_with_coords
from utils import haversine

OUTPUT_DIR = 'data/analysis'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def calculate_accessibility(crosswalks, schools):
    results = []

    for cw in crosswalks:
        school_dists = [haversine(cw['lat'], cw['lng'], s['lat'], s['lng']) for s in schools]
        if len(school_dists) == 0:
            school_score = 0
            min_school_dist = 1000
        else:
            min_school_dist = min(school_dists)
            school_score = max(0, 50 - (min_school_dist / 6))

        has_signal = 1 if cw['properties']['has_signal'] == 'Y' else 0
        signal_score = has_signal * 30

        lanes = cw['properties']['lanes'] or 1
        lane_score = max(0, 20 - (lanes - 1) * 5)

        total_score = school_score + signal_score + lane_score
        total_score = min(100, max(0, total_score))

        if total_score >= 80:
            grade = '우수'
        elif total_score >= 60:
            grade = '양호'
        elif total_score >= 40:
            grade = '보통'
        elif total_score >= 20:
            grade = '주의'
        else:
            grade = '위험'

        results.append({
            'id': cw['id'],
            'lat': cw['lat'],
            'lng': cw['lng'],
            'total_score': round(total_score, 1),
            'grade': grade,
            'details': {
                'school_access': round(school_score, 1),
                'signal_safety': signal_score,
                'lane_safety': lane_score,
                'min_school_dist': round(min_school_dist, 1)
            }
        })

    return results

def main():
    print("[accessibility_score] 시작...")

    crosswalks = get_crosswalks_with_coords()
    schools = get_schools_with_coords()
    print(f"  횡단보도 {len(crosswalks)}개, 학교 {len(schools)}개 로드")

    results = calculate_accessibility(crosswalks, schools)

    grades = {}
    for r in results:
        g = r['grade']
        grades[g] = grades.get(g, 0) + 1

    print(f"  등급 분포: {dict(sorted(grades.items(), key=lambda x: ['위험','주의','보통','양호','우수'].index(x[0]) if x[0] in ['위험','주의','보통','양호','우수'] else 99))}")

    avg_score = np.mean([r['total_score'] for r in results])
    print(f"  평균 점수: {avg_score:.1f}")

    output = {
        'generated_at': '2026-05-13',
        'total_crosswalks': len(results),
        'average_score': round(avg_score, 1),
        'grade_distribution': grades,
        'accessibility_scores': sorted(results, key=lambda x: x['total_score'], reverse=True)
    }

    path = os.path.join(OUTPUT_DIR, 'accessibility_score.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  저장 완료: {path}")

if __name__ == '__main__':
    main()
