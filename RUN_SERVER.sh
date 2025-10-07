
#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
export FLASK_APP=server/app.py
export FLASK_RUN_PORT=5000
python server/app.py
