import urllib.request
import json

r = urllib.request.urlopen('http://127.0.0.1:5000/api/makeups')
ms = json.loads(r.read())

print('=== 所有有关联考试的补考 ===')
for m in ms:
    if m['sourceExamId']:
        print(f'  #{m["id"]} {m["studentName"]} {m["originalSubject"]} - {m["status"]} sourceExamId={m["sourceExamId"]}')

print()
print('=== 张三的补考 ===')
for m in ms:
    if m['studentName'] == '张三':
        print(f'  #{m["id"]} {m["originalSubject"]} - {m["status"]} sourceExamId={m["sourceExamId"]}')
