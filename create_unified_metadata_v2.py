import csv
import json
import os
from collections import defaultdict
from datetime import datetime

def parse_school_csv(filepath):
    """Parse school CSV"""
    print("[1/4] Processing school data...")
    
    schools = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            kind = row.get('학교종류명', '')
            # Filter: 초등학교 only
            if '초등학교' in kind:
                address = row.get('도로명주소', '')
                schools.append({
                    "name": row.get('학교명', ''),
                    "address": address,
                    "type": kind,
                    "location": row.get('시도명', ''),
                    "district": row.get('관할조직명', ''),
                    "phone": row.get('전화번호', ''),
                    "lat": None,
                    "lon": None
                })
    
    print(f"  -> {len(schools)} elementary schools found")
    return schools

def parse_hotspot_csv(filepath):
    """Parse KOROAD accident hotspot data"""
    print("[2/4] Processing Hotspot data...")
    
    rows = []
    for enc in ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=enc, errors='replace') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                print(f"  -> Loaded with {enc}, {len(rows)} rows")
                break
        except Exception as e:
            continue
    
    if not rows:
        print("  -> Could not parse CSV")
        return []
    
    # Column analysis shows:
    # [5] = 지점명, [6] = 사고건수, [10] = 경도, [11] = 위도
    
    hotspots = []
    for row in rows:
        try:
            cols = list(row.values())
            if len(cols) >= 12:
                name = cols[5] if len(cols) > 5 else ''
                accidents = int(cols[6]) if len(cols) > 6 else 0
                
                lon = None
                lat = None
                
                for i, val in enumerate(cols):
                    try:
                        fval = float(val)
                        if 35 <= fval <= 38:
                            lat = fval
                        elif 125 <= fval <= 130:
                            lon = fval
                    except:
                        pass
                
                # Filter: Jeonju (전주) area - lat ~35.8, lon ~127.1
                is_jeonju = (lat and lon and 35.7 <= lat <= 35.9 and 127.0 <= lon <= 127.3) or \
                           ('전주' in name)
                
                if is_jeonju:
                    hotspots.append({
                        "name": name.strip() if name else 'Unknown',
                        "lat": lat,
                        "lon": lon,
                        "accidents": accidents,
                        "victims": 0
                    })
        except Exception as e:
            continue
    
    print(f"  -> {len(hotspots)} Jeonju hotspots found")
    return hotspots

def load_risk_metadata(filepath):
    """Load existing risk metadata"""
    print("[3/4] Loading risk metadata...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"  -> {data['metadata']['total_regions']} regions loaded")
    return data

def integrate_all_data(schools, hotspots, risk_metadata):
    """Create unified metadata"""
    
    metadata = {
        "metadata": {
            "version": "1.0",
            "created": datetime.now().strftime("%Y-%m-%d"),
            "sources": {
                "accidents": "전주시 일별시간별법정동별 교통사고 (2017~2019)",
                "schools": "전북특별자치도 학교기본정보",
                "hotspots": "KOROAD 사고다발지점"
            },
            "stats": {
                "total_accidents": risk_metadata['metadata']['total_accidents'],
                "total_regions": risk_metadata['metadata']['total_regions'],
                "total_schools": len(schools),
                "total_hotspots": len(hotspots)
            }
        },
        "risk_data": risk_metadata['regions'],
        "top_risk_regions": risk_metadata['top_risk_regions'],
        "schools": schools,
        "hotspots": hotspots
    }
    
    return metadata

def main():
    print("=" * 50)
    print("Unified Metadata Generator (v2)")
    print("=" * 50)
    
    # Files
    school_file = "학교기본정보.csv"
    hotspot_file = "어린이보호구역내 어린이.csv"
    risk_file = "output/risk_metadata.json"
    output_file = "output/unified_metadata.json"
    
    # Parse
    schools = parse_school_csv(school_file)
    hotspots = parse_hotspot_csv(hotspot_file)
    risk_metadata = load_risk_metadata(risk_file)
    
    # Integrate
    unified = integrate_all_data(schools, hotspots, risk_metadata)
    
    # Save
    os.makedirs("output", exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unified, f, ensure_ascii=False, indent=2)
    
    print(f"\n[DONE] -> {output_file}")
    print(f"  Schools: {len(schools)}")
    print(f"  Hotspots: {len(hotspots)}")
    print(f"  Risk Regions: {len(risk_metadata['regions'])}")

if __name__ == "__main__":
    main()