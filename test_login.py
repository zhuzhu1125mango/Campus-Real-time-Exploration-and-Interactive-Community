import requests
import json

url = "http://localhost:8000/api/users/users/login/"
headers = {"Content-Type": "application/json"}
data = {"username": "test2", "password": "test2123"}

try:
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
