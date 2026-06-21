import requests
r = requests.post("http://127.0.0.1:5000/api/ai/analyze",
    json={"device_id": "AQ-20260619-001", "hours": 24}, timeout=15)
print(r.status_code, r.text[:500])
