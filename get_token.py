import requests

# Get auth token
response = requests.post(
    "http://localhost:8000/api/v1/auth/token",
    data={
        "username": "demo@vedfin.com",
        "password": "admin123"
    }
)

if response.status_code == 200:
    token_data = response.json()
    token = token_data["access_token"]
    print(f"Token: {token}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
