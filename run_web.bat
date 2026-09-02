@echo off
echo Starting Tell Tims Survey Bot Web UI...
start http://127.0.0.1:8088
python "%~dp0server.py"
pause
