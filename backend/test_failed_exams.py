import urllib.request
import urllib.parse
import json

# 测试1: 同时输入姓名和证件号
params = urllib.parse.urlencode({
    'idNumber': '110101199901010011',
    'studentName': '张三'
})
url = f'http://127.0.0.1:5000/api/students/failed-exams?{params}'
print('测试1: 姓名+证件号')
try:
    r = urllib.request.urlopen(url)
    data = json.loads(r.read())
    print(f'  Count: {len(data)}')
    for e in data:
        print(f'    #{e["id"]} {e["description"]}')
except Exception as e:
    print(f'  Error: {e}')

# 测试2: 只输入姓名
params2 = urllib.parse.urlencode({'studentName': '张三'})
url2 = f'http://127.0.0.1:5000/api/students/failed-exams?{params2}'
print()
print('测试2: 只输入姓名')
try:
    r2 = urllib.request.urlopen(url2)
    data2 = json.loads(r2.read())
    print(f'  Count: {len(data2)}')
    for e in data2:
        print(f'    #{e["id"]} {e["description"]}')
except Exception as e:
    print(f'  Error: {e}')

# 测试3: 只输入证件号
params3 = urllib.parse.urlencode({'idNumber': '110101199901010011'})
url3 = f'http://127.0.0.1:5000/api/students/failed-exams?{params3}'
print()
print('测试3: 只输入证件号')
try:
    r3 = urllib.request.urlopen(url3)
    data3 = json.loads(r3.read())
    print(f'  Count: {len(data3)}')
    for e in data3:
        print(f'    #{e["id"]} {e["description"]}')
except Exception as e:
    print(f'  Error: {e}')
