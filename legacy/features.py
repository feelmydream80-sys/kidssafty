import numpy as np
from .utils import haversine

def extract_features(point, crosswalk_coords, schools, accident_dongjak):
    """
    격자점의 특징 추출
    ⚠️ 문제점: acc_near_dist, acc_count_500m는 데이터 오염(leakage) 발생
    - acc_near_dist: 사고다발지역 최소 거리 (라벨과 100% 상관)
    - acc_count_500m: 500m 내 사고 건수 (라벨 정보 누출)
    📌 향후 수정: 두 피처 제거 필요
    """
    lat, lng = point['lat'], point['lng']
    features = {}
    
    # 횡단보도 관련 (50m 내)
    cw_near = [c for c in crosswalk_coords if haversine(lat, lng, c['lat'], c['lng']) <= 50]
    features['cw_count_50m'] = len(cw_near)
    features['cw_signal_ratio'] = np.mean([c['signal'] for c in cw_near]) if cw_near else 0
    features['cw_avg_lanes'] = np.mean([c['lanes'] for c in cw_near]) if cw_near else 1
    
    # 학교 관련 (300m 내)
    school_near = [s for s in schools if haversine(lat, lng, s['lat'], s['lng']) <= 300]
    features['school_count_300m'] = len(school_near)
    if school_near:
        min_school_dist = min([haversine(lat, lng, s['lat'], s['lng']) for s in school_near])
        features['min_school_dist'] = min_school_dist
    else:
        features['min_school_dist'] = 500
    
    # ⚠️ 데이터 오염 피처 (향후 제거)
    acc_near = []
    for _, row in accident_dongjak.iterrows():
        dist = haversine(lat, lng, row['lat'], row['lng'])
        if dist <= 500:
            acc_near.append({'dist': dist, 'accidents': int(row['사고건수']), 'casualties': int(row['사상자수'])})
    features['acc_count_500m'] = sum([a['accidents'] for a in acc_near])
    features['acc_near_dist'] = min([a['dist'] for a in acc_near]) if acc_near else 1000
    
    return features
