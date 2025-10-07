
import requests, json, sys
BASE = sys.argv[1] if len(sys.argv)>1 else "http://localhost:8000"
r = requests.post(BASE+"/api/self_audit/run", timeout=10)
print(r.status_code, r.text)
