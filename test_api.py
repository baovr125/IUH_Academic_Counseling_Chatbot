import requests

res = requests.post("http://localhost:8001/api/auth/login", json={
    'identifier': 'testuser123@gmail.com',
    'password': 'TestPassword123!'
})
token = res.json().get('data', {}).get('token')

res2 = requests.post("http://localhost:8000/api/v1/translate/stream", json={
    "text": "Random unknown word",
    "source_lang": "en",
    "target_lang": "vi",
    "domain": "Công nghệ Thông tin (IT)"
}, headers={"Authorization": f"Bearer {token}"}, stream=True)

for line in res2.iter_lines():
    if line:
        print(line.decode('utf-8'))
