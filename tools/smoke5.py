
import requests, time, json, sys
BASE = sys.argv[1] if len(sys.argv)>1 else "http://localhost:8000"
res=[]
for i in range(5):
    try:
        r = requests.post(BASE+"/api/tests/smoke", timeout=10)
        res.append({"round":i+1,"status":r.status_code})
        time.sleep(0.3)
    except Exception as e:
        res.append({"round":i+1,"error":str(e)})
print(json.dumps(res, indent=2))
