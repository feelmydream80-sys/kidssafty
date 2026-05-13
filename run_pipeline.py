"""
Kids Safety Data Pipeline
==========================
Layer 1: 원천 CSV → JSON 변환
Layer 2: JSON 통합 → locations.json
Layer 3: 분석 파이프라인 실행 → data/analysis/*.json
"""
import subprocess
import sys
import time

steps = [
    ('Layer 1-1', '학교별위치정보 변환', ['python', 'convert_schools.py']),
    ('Layer 1-2', '어린이보호구역 변환', ['python', 'convert_protection_zones.py']),
    ('Layer 1-3', '횡단보도 변환', ['python', 'convert_crosswalks.py']),
    ('Layer 1-4', '사고다발지역 변환', ['python', 'convert_accidents.py']),
    ('Layer 2', '통합 위치정보 생성', ['python', 'merge_locations.py']),
    ('Layer 3-1', '학교 안전등급 분석', ['python', 'risk_prediction/school_safety_grader.py']),
    ('Layer 3-2', '횡단보도 접근성', ['python', 'risk_prediction/accessibility_score.py']),
    ('Layer 3-3', '신호등 우선순위', ['python', 'risk_prediction/signal_priority.py']),
    ('Layer 3-4', '안전 지수', ['python', 'risk_prediction/safety_index.py']),
    ('Layer 3-5', '위험 밀도 맵', ['python', 'risk_prediction/density_mapper.py']),
]

total_start = time.time()
success = 0
fail = 0

print('=' * 60)
print('  Kids Safety Data Pipeline')
print('=' * 60)

for layer, desc, cmd in steps:
    print(f'\n--- [{layer}] {desc} ---')
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        elapsed = time.time() - start
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                print(f'  {line}')
            if result.stderr.strip():
                print(f'  [stderr] {result.stderr.strip()[-200:]}')
            print(f'  [OK] 완료 ({elapsed:.1f}초)')
            success += 1
        else:
            print(f'  [FAIL] 실패 (exit code {result.returncode})')
            print(f'  {result.stderr[-500:]}')
            fail += 1
    except Exception as e:
        print(f'  [FAIL] 오류: {e}')
        fail += 1

total_elapsed = time.time() - total_start
print(f'\n{"=" * 60}')
print(f'  파이프라인 완료: {success}성공 / {fail}실패 (총 {total_elapsed:.1f}초)')
print(f'{"=" * 60}')
