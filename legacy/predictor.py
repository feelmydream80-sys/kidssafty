import json
import numpy as np
from .utils import haversine

def predict_risk_zones(model, X, grid_points, threshold=0.7):
    """전체 격자점 위험 예측"""
    predictions = model.predict(X)
    
    risk_zones = []
    for i, point in enumerate(grid_points):
        if predictions[i] >= threshold:
            risk_zones.append({
                'lat': point['lat'],
                'lng': point['lng'],
                'risk_score': round(float(predictions[i]), 3)
            })
    return risk_zones

def cluster_risk_zones(risk_zones):
    """인접 점 클러스터링 (50m 이내 묶기)"""
    clusters = []
    visited = [False] * len(risk_zones)
    
    for i in range(len(risk_zones)):
        if visited[i]:
            continue
        cluster = [risk_zones[i]]
        visited[i] = True
        
        for j in range(i+1, len(risk_zones)):
            if visited[j]:
                continue
            dist = haversine(
                risk_zones[i]['lat'], risk_zones[i]['lng'],
                risk_zones[j]['lat'], risk_zones[j]['lng']
            )
            if dist <= 50:
                cluster.append(risk_zones[j])
                visited[j] = True
        
        if cluster:
            avg_lat = np.mean([p['lat'] for p in cluster])
            avg_lng = np.mean([p['lng'] for p in cluster])
            avg_score = np.mean([p['risk_score'] for p in cluster])
            clusters.append({
                'center_lat': round(avg_lat, 6),
                'center_lng': round(avg_lng, 6),
                'risk_score': round(avg_score, 3),
                'point_count': len(cluster)
            })
    return clusters

def save_results(clusters, output_path='data/predicted_risk_zones.json'):
    """결과 저장"""
    result = {
        'generated_at': '2026-05-06',
        'model': 'XGBRegressor',
        'total_predicted_zones': len(clusters),
        'clusters': clusters
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result
