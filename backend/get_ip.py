import requests
try:
    print(requests.get('https://api.ipify.org').text)
except Exception as e:
    print(f"Could not get IP: {e}")
