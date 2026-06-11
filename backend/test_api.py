import urllib.request
import urllib.parse
import json

print('=== 测试1: 检查后端服务是否运行 ===')
try:
    r = urllib.request.urlopen('http://127.0.0.1:5000/api/makeups')
    print(f'OK: {r.status}')
except Exception as e:
    print(f'FAIL: {e}')

print()
print('=== 测试2: failed-exams 并集查询 ===')
params = urllib.parse.urlencode({
    'idNumber': '110101199901010011',
    'studentName': '张三'
})
url = f'http://127.0.0.1:5000/api/students/failed-exams?{params}'
try:
    r = urllib.request.urlopen(url)
    data = json.loads(r.read())
    print(f'OK: {r.status}, 共 {len(data)} 条')
    for e in data:
        print(f'  #{e["id"]} {e["description"]}')
except Exception as e:
    print(f'FAIL: {e}')

print()
print('=== 测试3: 取消补考并验证释放关联 ===')

from app import create_app, db
from app.models import Makeup, ExamRecord

app = create_app()
with app.app_context():
    # 找一个有关联考试的补考
    makeup = Makeup.query.filter(Makeup.source_exam_id.isnot(None)).first()
    if makeup:
        print(f'找到补考 #{makeup.id}，关联考试 #{makeup.source_exam_id}')
        print(f'当前状态: {makeup.status}')
        
        # 用API取消
        import urllib.request as req
        import json as j
        data = j.dumps({'status': '已取消'}).encode('utf-8')
        request = req.Request(
            f'http://127.0.0.1:5000/api/makeups/{makeup.id}',
            data=data,
            method='PATCH',
            headers={'Content-Type': 'application/json'}
        )
        try:
            resp = req.urlopen(request)
            result = j.loads(resp.read())
            print(f'取消成功: status={result["status"]}, sourceExamId={result["sourceExamId"]}')
        except Exception as e:
            print(f'取消失败: {e}')
        
        # 验证source_exam_id被清除
        db.session.refresh(makeup)
        print(f'数据库中 source_exam_id = {makeup.source_exam_id}')
        
        # 验证该考试重新出现在可选列表
        params = urllib.parse.urlencode({'idNumber': makeup.id_number})
        url2 = f'http://127.0.0.1:5000/api/students/failed-exams?{params}'
        r2 = urllib.request.urlopen(url2)
        exams = json.loads(r2.read())
        exam_ids = [e['id'] for e in exams]
        if makeup.source_exam_id is None:
            original_exam_id = 13  # 之前的考试
            if original_exam_id in exam_ids:
                print(f'OK: 考试 #{original_exam_id} 已重新出现在可选列表中')
            else:
                print(f'WARN: 考试 #{original_exam_id} 不在可选列表中 (列表: {exam_ids})')
    else:
        print('没有找到有关联考试的补考')
