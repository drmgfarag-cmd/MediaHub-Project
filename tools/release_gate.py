
import requests, sys, json
BASE = sys.argv[1] if len(sys.argv)>1 else "http://localhost:8000"
r = requests.post(BASE+"/api/release/gate", timeout=15)
print(r.status_code, json.dumps(r.json(), indent=2))
