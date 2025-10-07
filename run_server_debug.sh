
#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate
export PYTHONFAULTHANDLER=1
export PYTHONWARNINGS=default
python -X dev server/app.py
