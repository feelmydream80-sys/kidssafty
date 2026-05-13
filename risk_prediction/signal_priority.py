import pandas as pd
import numpy as np
import json
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from data_loader import get_schools_with_coords, get_crosswalks_with_coords, get_accidents_with_coords
from utils import haversine

OUTPUT_DIR = 'data/analysis'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_features(crosswalks, schools, accidents):
    results = []

    for cw in crosswalks:
        school_dists = [haversine(cw['lat'], cw['lng'], s['lat'], s['lng']) for s in schools]
        min_school_dist = min(school_dists) if school_dists else 1000
        nearby_schools = sum(1 for d in school_dists if d <= 300)

        acc_near = []
        for a in accidents:
            dist = haversine(cw['lat'], cw['lng'], a['lat'], a['lng'])
            if dist <= 500:
                acc_near.append(dist)
        min_acc_dist = min(acc_near) if acc_near else 1000

        has_signal = 1 if cw['properties']['has_signal'] == 'Y' else 0
        need_signal = 0
        if has_signal == 0:
            if min_school_dist <= 300 or min_acc_dist <= 500:
                need_signal = 1

        results.append({
            'id': cw['id'],
            'lat': cw['lat'],
            'lng': cw['lng'],
            'has_signal': has_signal,
            'lanes': cw['properties']['lanes'] or 1,
            'min_school_dist': min_school_dist,
            'nearby_schools': nearby_schools,
            'min_accident_dist': min_acc_dist,
            'need_signal': need_signal
        })

    return results

def predict_priority(data):
    df = pd.DataFrame(data)
    X = df[['lanes', 'min_school_dist', 'nearby_schools', 'min_accident_dist']].values
    y = df['need_signal'].values

    if sum(y) > 0:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        proba = model.predict_proba(X)[:, 1]
        df['priority_score'] = proba
    else:
        df['priority_score'] = df.apply(
            lambda row: (1 if row['has_signal'] == 0 else 0) *
                          (100 - min(row['min_school_dist'], 100)) / 100,
            axis=1
        )

    df_sorted = df.sort_values('priority_score', ascending=False)
    return df_sorted.to_dict('records')

def main():
    print("[signal_priority] 시작...")

    crosswalks = get_crosswalks_with_coords()
    schools = get_schools_with_coords()
    accidents = get_accidents_with_coords()
    print(f"  횡단보도 {len(crosswalks)}개, 학교 {len(schools)}개, 사고지역 {len(accidents)}개 로드")

    data = create_features(crosswalks, schools, accidents)
    results = predict_priority(data)

    output = {
        'generated_at': '2026-05-13',
        'total_crosswalks': len(results),
        'need_signal_count': sum(1 for r in results if r['need_signal'] == 1),
        'top_20_priority': results[:20],
        'all_crosswalks': results
    }

    path = os.path.join(OUTPUT_DIR, 'signal_priority.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  신호등 설치 필요: {output['need_signal_count']}개")
    print(f"  저장 완료: {path}")

if __name__ == '__main__':
    main()
