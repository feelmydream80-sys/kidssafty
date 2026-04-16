import csv
import json
import os
from collections import defaultdict
from datetime import datetime

# 설정
INPUT_FILE = "도로교통공단_전북 전주시 일별 시간별 교통사고 현황_20191231.csv"
OUTPUT_FILE = "output/risk_metadata.json"

# 인코딩 변환 (CP949 → UTF-8 저장)
def convert_encoding():
    """CSV 파일을 CP949에서 UTF-8로 변환하여 반환"""
    with open(INPUT_FILE, 'r', encoding='cp949', errors='ignore') as f:
        reader = csv.DictReader(f)
        return list(reader)

def process_accident_data(rows):
    """시간대별 · 법정동별 사고 데이터 처리"""
    
    # 1. 법정동별 사고 통계
    region_stats = defaultdict(lambda: {
        'total': 0,
        'by_hour': defaultdict(int),
        'by_year': defaultdict(int),
        'victims': {'dead': 0, 'injured': 0, 'serious': 0, 'minor': 0}
    })
    
    for row in rows:
        # 컬럼명 정규화 (실제 컬럼명 확인 필요)
        dong = row.get('법정동명', row.get('발생지_법정동', '')).strip()
        hour = row.get('발생시간', row.get('발생시간대', '')).strip()
        year = row.get('발생일', '')[:4] if row.get('발생일') else ''
        
        # 사고 건수
        try:
            accidents = int(row.get('사고건수', 1))
        except:
            accidents = 1
        
        if dong and hour:
            region_stats[dong]['total'] += accidents
            region_stats[dong]['by_hour'][hour.zfill(2)] += accidents
            
            if year:
                region_stats[dong]['by_year'][year] += accidents
            
            # 사상자 수
            region_stats[dong]['victims']['dead'] += int(row.get('사망자수', 0) or 0)
            region_stats[dong]['victims']['injured'] += int(row.get('부상신고자수', 0) or 0)
            region_stats[dong]['victims']['serious'] += int(row.get('중상자수', 0) or 0)
            region_stats[dong]['victims']['minor'] += int(row.get('경상자수', 0) or 0)
    
    return region_stats

def calculate_risk(region_stats):
    """위험도 계산 (설계서 4장 기준)"""
    
    risk_data = {}
    
    for dong, data in region_stats.items():
        total = data['total']
        if total == 0:
            continue
        
        # 통학 시간대 (07~17시)만 필터링
        school_hours = {h: cnt for h, cnt in data['by_hour'].items() 
                       if 7 <= int(h) <= 17}
        school_total = sum(school_hours.values())
        
        if school_total == 0:
            continue
        
        # 시간대별 위험도 (통학 시간대 내 비율)
        risk_by_hour = {}
        for hour, count in school_hours.items():
            score = count / school_total
            if score >= 0.10:
                grade = "HIGH"
            elif score >= 0.06:
                grade = "MID"
            else:
                grade = "LOW"
            
            risk_by_hour[hour] = {
                "count": count,
                "score": round(score, 3),
                "grade": grade
            }
        
        # 전체 시간대 위험도 (참고용)
        all_risk_by_hour = {}
        for hour, count in data['by_hour'].items():
            score = count / total
            all_risk_by_hour[hour] = {
                "count": count,
                "score": round(score, 3)
            }
        
        risk_data[dong] = {
            "total_accidents": total,
            "school_time_accidents": school_total,
            "risk_by_hour": risk_by_hour,
            "all_hours": all_risk_by_hour,
            "victims": data['victims']
        }
    
    return risk_data

def generate_metadata(risk_data):
    """메타데이터 생성"""
    
    # 전체 통계
    total_accidents = sum(d['total_accidents'] for d in risk_data.values())
    
    # 상위 위험 지역 (통학 시간대 사고 많은 순)
    top_risks = sorted(
        [(dong, d['school_time_accidents']) for dong, d in risk_data.items()],
        key=lambda x: x[1], reverse=True
    )[:10]
    
    metadata = {
        "metadata": {
            "version": "1.0",
            "created": datetime.now().strftime("%Y-%m-%d"),
            "source": "전주시 일별시간별법정동별 교통사고 (2017~2019)",
            "total_accidents": total_accidents,
            "total_regions": len(risk_data),
            "note": "통학 시간대(07~17시) 위험도 중심 분석"
        },
        "regions": risk_data,
        "top_risk_regions": [{"region": r[0], "accidents": r[1]} for r in top_risks]
    }
    
    return metadata

def main():
    print("=" * 50)
    print("위험도 메타데이터 생성 시작")
    print("=" * 50)
    
    # 1. 데이터 로드
    print("\n[1/4] 데이터 로드 중...")
    rows = convert_encoding()
    print(f"  → 총 {len(rows)}건 로드됨")
    
    # 2. 데이터 처리
    print("\n[2/4] 데이터 처리 중...")
    region_stats = process_accident_data(rows)
    print(f"  → {len(region_stats)}개 법정동 처리됨")
    
    # 3. 위험도 계산
    print("\n[3/4] 위험도 계산 중...")
    risk_data = calculate_risk(region_stats)
    print(f"  → {len(risk_data)}개 지역 위험도 산출됨")
    
    # 4. 메타데이터 생성
    print("\n[4/4] 메타데이터 생성 중...")
    metadata = generate_metadata(risk_data)
    
    # 저장
    os.makedirs("output", exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\n[COMPLETE] -> {OUTPUT_FILE}")
    print(f"  - Total accidents: {metadata['metadata']['total_accidents']}")
    print(f"  - Total regions: {metadata['metadata']['total_regions']}")
    
    # Top risk regions
    print("\n[TOP RISK REGIONS]:")
    for item in metadata['top_risk_regions'][:5]:
        print(f"  {item['region']}: {item['accidents']} accidents")

if __name__ == "__main__":
    main()