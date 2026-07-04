import json
import urllib.request

# Login
req = urllib.request.Request(
    'http://localhost:8000/api/users/users/login/',
    data=json.dumps({'username': 'testuser1', 'password': 'Test123456'}).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())
print('login:', resp.status, data.get('user', {}).get('username'))
access = data.get('access')

# Get conversation
req2 = urllib.request.Request(
    'http://localhost:8000/api/users/messages/conversation/?user_id=9&page=1&page_size=20',
    headers={'Authorization': f'Bearer {access}'}
)
try:
    resp2 = urllib.request.urlopen(req2)
    print('conversation:', resp2.status, json.loads(resp2.read()))
except urllib.error.HTTPError as e:
    err_body = e.read().decode('utf-8')
    with open('conversation_error.html', 'w', encoding='utf-8') as f:
        f.write(err_body)
    print('conversation error:', e.code, 'see conversation_error.html')
