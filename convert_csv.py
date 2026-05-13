import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('12_24_child.csv', 'rb') as f:
    content = f.read()

try:
    decoded = content.decode('utf-8')
except UnicodeDecodeError:
    decoded = content.decode('euc-kr')

with open('data/child_safety_zones.csv', 'w', encoding='utf-8') as f:
    f.write(decoded)

print("CSV 변환 완료")
