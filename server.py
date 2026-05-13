# server.py - 데이터 업로드 서버 (Flask)
# 실행: python server.py
# 웹에서 파일 업로드 받아 ori_data/ 저장 + run_pipeline.py 실행

import os, sys, json, uuid, threading, time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = 'ori_data'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE_MAP = {
    'schools': {
        'dir_file': '학교별위치정보_202412270000001.csv',
        'pipeline_script': 'convert_schools.py',
        'expected_headers': ['학교코드', '학교코드명', '위도값', '경도값']
    },
    'protection_zones': {
        'dir_file': '서울특별시 동작구_어린이보호구역_20200206.csv',
        'pipeline_script': 'convert_protection_zones.py',
        'expected_headers': ['시설종류', '대상시설명', '위도', '경도', '카메라 설치여부(CCTV)']
    },
    'crosswalks': {
        'dir_file': '서울특별시_동작구_횡단보도_20260306.csv',
        'pipeline_script': 'convert_crosswalks.py',
        'expected_headers': ['횡단보도관리번호', '소재지도로명주소', '위도', '경도', '보행자신호등유무']
    },
    'accidents': {
        'dir_file': '전국교통사고다발지역표준데이터.csv',
        'pipeline_script': 'convert_accidents.py',
        'expected_headers': ['사고다발지역관리번호', '사고다발지역시도시군구', '위도', '경도', '사고건수']
    }
}

pipeline_running = False
pipeline_result = None

def run_pipeline_async():
    global pipeline_running, pipeline_result
    pipeline_running = True
    pipeline_result = None
    try:
        os.chdir(BASE_DIR)
        import subprocess
        result = subprocess.run(
            [sys.executable, 'run_pipeline.py'],
            capture_output=True, text=True, timeout=120
        )
        pipeline_result = {
            'success': result.returncode == 0,
            'stdout': result.stdout[-2000:] if result.stdout else '',
            'stderr': result.stderr[-2000:] if result.stderr else '',
            'returncode': result.returncode
        }
    except Exception as e:
        pipeline_result = {'success': False, 'error': str(e)}
    finally:
        pipeline_running = False

def validate_headers(headers, source_key):
    info = SOURCE_MAP.get(source_key)
    if not info:
        return {'match': False, 'reason': 'unknown_source'}
    expected = info['expected_headers']
    matched = sum(1 for h in expected if h in headers)
    ratio = matched / len(expected)
    missing = [h for h in expected if h not in headers]
    return {
        'match': ratio >= 0.6,
        'ratio': round(ratio, 2),
        'matched': matched,
        'total': len(expected),
        'missing': missing,
        'detected_as': source_key if ratio >= 0.6 else None
    }

@app.route('/')
def serve_index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(BASE_DIR, path)

@app.route('/api/status', methods=['GET'])
def status():
    info = {}
    for key, val in SOURCE_MAP.items():
        fpath = os.path.join(BASE_DIR, UPLOAD_DIR, val['dir_file'])
        if os.path.exists(fpath):
            info[key] = {
                'exists': True,
                'size': os.path.getsize(fpath),
                'modified': time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(fpath)))
            }
        else:
            info[key] = {'exists': False}
    return jsonify({
        'server_ok': True,
        'pipeline_running': pipeline_running,
        'files': info
    })

@app.route('/api/validate', methods=['POST'])
def validate():
    data = request.get_json()
    headers = data.get('headers', [])
    source_key = data.get('source_key', '')
    
    if source_key and source_key in SOURCE_MAP:
        result = validate_headers(headers, source_key)
    else:
        # 자동 감지
        results = []
        for key in SOURCE_MAP:
            r = validate_headers(headers, key)
            if r['match']:
                results.append({'key': key, 'ratio': r['ratio'], 'missing': r['missing']})
        if results:
            best = max(results, key=lambda x: x['ratio'])
            result = {'match': True, 'ratio': best['ratio'], 'detected_as': best['key'], 'missing': best['missing']}
        else:
            result = {'match': False, 'options': list(SOURCE_MAP.keys())}
    
    return jsonify(result)

@app.route('/api/upload', methods=['POST'])
def upload():
    global pipeline_running
    
    if pipeline_running:
        return jsonify({'success': False, 'error': 'Pipeline already running'}), 409
    
    source_key = request.form.get('source_key')
    if not source_key or source_key not in SOURCE_MAP:
        return jsonify({'success': False, 'error': 'Invalid source key'}), 400
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Empty filename'}), 400
    
    info = SOURCE_MAP[source_key]
    save_path = os.path.join(BASE_DIR, UPLOAD_DIR, info['dir_file'])
    
    # 백업
    backup_dir = os.path.join(BASE_DIR, UPLOAD_DIR, 'backup')
    os.makedirs(backup_dir, exist_ok=True)
    if os.path.exists(save_path):
        import shutil
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        backup_name = f'{timestamp}_{info["dir_file"]}'
        shutil.copy2(save_path, os.path.join(backup_dir, backup_name))
    
    file.save(save_path)
    
    # 비동기 파이프라인 실행
    thread = threading.Thread(target=run_pipeline_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'source_key': source_key, 'message': f'{info["dir_file"]} saved, pipeline started'})

@app.route('/api/pipeline-status', methods=['GET'])
def pipeline_status():
    global pipeline_running, pipeline_result
    return jsonify({
        'running': pipeline_running,
        'result': pipeline_result
    })

if __name__ == '__main__':
    print('=' * 50)
    print('  Kids Safety Data Upload Server')
    print('  http://localhost:5000')
    print('=' * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
