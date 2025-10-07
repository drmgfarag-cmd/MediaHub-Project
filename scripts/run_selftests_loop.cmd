@echo off
echo Running smoke tests 5x...
for /l %%i in (1,1,5) do (
  echo Pass %%i
  curl -s http://127.0.0.1:5000/integrations/self_tests/js_lint || echo JS lint check requires server running
)
echo Collecting Support Pack...
python scripts\js_lint.py > logs\js_lint.json
pause
