import urllib.request
import urllib.parse
import json

def test_failed_exams_union():
    print('=== 测试1: failed-exams 并集查询 ===')
    
    params = urllib.parse.urlencode({
        'idNumber': '110101199901010011',
        'studentName': '张三'
    })
    url = f'http://127.0.0.1:5000/api/students/failed-exams?{params}'
    
    try:
        r = urllib.request.urlopen(url)
        data = json.loads(r.read())
        print(f'Status: {r.status}')
        print(f'Count: {len(data)}')
        for e in data:
            print(f'  #{e["id"]} {e["description"]}')
    except Exception as e:
        print(f'Error: {e}')

def test_cancel_makeup():
    print()
    print('=== 测试2: 取消补考释放关联考试 ===')
    
    # 先找一个有关联考试且未取消的补考
    list_url = 'http://127.0.0.1:5000/api/makeups'
    r = urllib.request.urlopen(list_url)
    makeups = json.loads(r.read())
    
    target = None
    for m in makeups:
        if m['sourceExamId'] and m['status'] != '已取消':
            target = m
            break
    
    if not target:
        print('没有找到有关联考试的未取消补考')
        return
    
    print(f'选中补考 #{target["id"]}: {target["studentName"]} {target["originalSubject"]}')
    print(f'  状态: {target["status"]}')
    print(f'  关联考试: #{target["sourceExamId"]}')
    
    # 取消前，验证该考试不在可选列表
    params = urllib.parse.urlencode({'idNumber': target['idNumber']})
    before_url = f'http://127.0.0.1:5000/api/students/failed-exams?{params}'
    r_before = urllib.request.urlopen(before_url)
    before = json.loads(r_before.read())
    before_ids = [e['id'] for e in before]
    print(f'  取消前可选考试数: {len(before)}, 考试#{target["sourceExamId"]}在列表中: {target["sourceExamId"] in before_ids}')
    
    # 取消补考
    data = json.dumps({'status': '已取消'}).encode('utf-8')
    request = urllib.request.Request(
        f'http://127.0.0.1:5000/api/makeups/{target["id"]}',
        data=data,
        method='PATCH',
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        resp = urllib.request.urlopen(request)
        result = json.loads(resp.read())
        print(f'  取消成功: status={result["status"]}, sourceExamId={result["sourceExamId"]}')
    except Exception as e:
        print(f'  取消失败: {e}')
        return
    
    # 取消后，验证该考试重新出现在可选列表
    r_after = urllib.request.urlopen(before_url)
    after = json.loads(r_after.read())
    after_ids = [e['id'] for e in after]
    print(f'  取消后可选考试数: {len(after)}, 考试#{target["sourceExamId"]}在列表中: {target["sourceExamId"] in after_ids}')
    
    if target['sourceExamId'] in after_ids:
        print('  OK: 考试已成功释放，重新出现在可选列表中')
    else:
        print('  FAIL: 考试未出现在可选列表中')

if __name__ == '__main__':
    test_failed_exams_union()
    test_cancel_makeup()
