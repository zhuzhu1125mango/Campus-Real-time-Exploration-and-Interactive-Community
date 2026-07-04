"""全链路功能测试脚本"""
import json
import urllib.request
import urllib.error
from urllib.parse import quote

BASE_URL = 'http://localhost:8000/api'


def request_json(method, path, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    url = f'{BASE_URL}{path}'
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {'raw': body[:500]}


def login(username, password):
    status, data = request_json('POST', '/users/users/login/', {'username': username, 'password': password})
    if status != 200:
        raise Exception(f'登录失败 {username}: {status} {data}')
    return data['access'], data['refresh'], data['user']


def test_auth():
    print('\n=== 测试注册/登录 ===')
    # 登录已有测试用户
    access1, _, user1 = login('testuser1', 'Test123456')
    access2, _, user2 = login('testuser2', 'Test123456')
    print(f'登录成功: user1={user1["id"]}, user2={user2["id"]}')
    return access1, access2, user1, user2


def test_private_messages(access1, access2, user1, user2):
    print('\n=== 测试私信 ===')
    # user1 发送消息给 user2
    status, data = request_json('POST', f'/users/messages/{user2["id"]}/', {'content': '你好，这是一条测试私信'}, token=access1)
    print(f'发送消息: {status}')
    assert status == 201, f'发送消息失败: {data}'

    # user2 获取会话列表
    status, data = request_json('GET', '/users/messages/conversations/', token=access2)
    print(f'user2 会话列表: {status}, 数量={len(data)}')
    assert status == 200
    assert len(data) > 0, '会话列表为空'
    assert data[0]['last_message']['content'] == '你好，这是一条测试私信'

    # user2 获取与 user1 的对话
    status, data = request_json('GET', f'/users/messages/conversation/?user_id={user1["id"]}&page=1&page_size=20', token=access2)
    print(f'user2 查看对话: {status}, 消息数={len(data["messages"])}')
    assert status == 200
    assert len(data['messages']) > 0

    # user2 回复
    status, data = request_json('POST', f'/users/messages/{user1["id"]}/', {'content': '收到，谢谢！'}, token=access2)
    print(f'user2 回复: {status}')
    assert status == 201

    # 未读数
    status, data = request_json('GET', '/users/messages/unread_count/', token=access1)
    print(f'user1 未读数: {status}, count={data.get("unread_count")}')
    assert status == 200


def test_favorite_schools(access1):
    print('\n=== 测试院校收藏 ===')
    # 获取学校列表（schools 路由根视图集）
    status, data = request_json('GET', '/schools/?page=1&page_size=1')
    if status != 200 or not data.get('results'):
        print(f'获取学校列表失败或为空: {status} {data}')
        return
    school = data['results'][0]
    school_id = school['id']
    print(f'测试学校: {school.get("name")} (id={school_id})')

    # 收藏
    status, data = request_json('POST', '/users/favorites/add_favorite/', {
        'content_type': 'schools.school',
        'object_id': school_id,
        'category': 'school'
    }, token=access1)
    print(f'收藏学校: {status}')

    # 获取收藏列表
    status, data = request_json('GET', '/users/favorites/by_category/?category=school', token=access1)
    print(f'收藏列表: {status}, 数量={len(data) if isinstance(data, list) else "N/A"}')
    if status == 200 and isinstance(data, list):
        assert any(str(item.get('object_id')) == str(school_id) or item.get('content_object', {}).get('id') == school_id for item in data), '收藏列表中未找到学校'

    # 取消收藏
    status, data = request_json('DELETE', '/users/favorites/remove_favorite/', {
        'content_type': 'schools.school',
        'object_id': school_id
    }, token=access1)
    print(f'取消收藏: {status}')


def test_forum(access1):
    print('\n=== 测试论坛 ===')
    # 获取板块列表
    status, data = request_json('GET', '/boards/?page=1&page_size=1')
    if status != 200 or not data.get('results'):
        print(f'获取板块列表失败或为空: {status}')
        return
    board = data['results'][0]
    board_id = board['id']
    print(f'测试板块: {board.get("name")} (id={board_id})')

    # 获取主题列表
    status, data = request_json('GET', f'/boards/{board_id}/topics/?page=1&page_size=1')
    print(f'主题列表: {status}')

    # 搜索
    status, data = request_json('GET', f'/posts/?search={quote("测试")}&ordering=-created_at')
    print(f'搜索帖子: {status}, 数量={len(data.get("results", []))}')

    # 发帖（需要登录）
    status, data = request_json('POST', '/topics/', {
        'board': board_id,
        'title': '全链路测试主题',
        'content': '这是一个自动化测试帖子内容。'
    }, token=access1)
    print(f'发帖: {status}')
    if status == 201:
        topic_id = data['id']
        # 回复
        status, data = request_json('POST', '/posts/', {
            'topic': topic_id,
            'content': '测试回复内容'
        }, token=access1)
        print(f'回帖: {status}')


def test_learning(access1):
    print('\n=== 测试学习模块 ===')
    # 游客访问课程列表
    status, data = request_json('GET', '/learning/courses/?page=1&page_size=1')
    print(f'游客课程列表: {status}')
    if status != 200 or not data.get('results'):
        print('课程列表为空或失败，跳过后续测试')
        return

    course = data['results'][0]
    course_id = course['id']

    # 游客访问详情
    status, data = request_json('GET', f'/learning/courses/{course_id}/')
    print(f'游客课程详情: {status}')
    assert status == 200, '游客应能访问课程详情'

    # 游客访问章节
    status, data = request_json('GET', f'/learning/courses/{course_id}/chapters/')
    print(f'游客课程章节: {status}')

    # 登录后报名（如未报名）
    status, data = request_json('POST', '/learning/enrollments/', {'course': course_id}, token=access1)
    print(f'报名课程: {status}, {data.get("message", data.get("detail", ""))}')


def test_content(access1):
    print('\n=== 测试内容发布 ===')
    # 获取内容列表（游客）
    status, data = request_json('GET', '/content/contents/?page=1&page_size=1')
    print(f'内容列表: {status}')

    # 获取内容类型
    status, data = request_json('GET', '/content/content-types/?page=1&page_size=1')
    print(f'内容类型: {status}')
    if status != 200 or not data.get('results'):
        print('没有可用的内容类型，跳过后续测试')
        return
    content_type_id = data['results'][0]['id']

    # 登录发布
    status, data = request_json('POST', '/content/contents/', {
        'title': '全链路测试内容',
        'content': '<p>自动化测试内容正文</p>',
        'content_type': content_type_id,
        'is_published': True
    }, token=access1)
    print(f'发布内容: {status}')
    if status == 201:
        content_id = data['id']
        status, data = request_json('GET', f'/content/contents/{content_id}/')
        print(f'内容详情: {status}')


def main():
    access1, access2, user1, user2 = test_auth()
    test_private_messages(access1, access2, user1, user2)
    test_favorite_schools(access1)
    test_forum(access1)
    test_learning(access1)
    test_content(access1)
    print('\n=== 全链路测试完成 ===')


if __name__ == '__main__':
    main()
