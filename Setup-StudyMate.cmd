@echo off
setlocal
cd /d "%~dp0"
python -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11 or newer is required'"
if errorlevel 1 goto failed
if not exist ".venv\Scripts\python.exe" python -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements-lock.txt
if errorlevel 1 goto failed
echo Setup complete. Open Start-StudyMate.cmd to run the offline demo.
pause
exit /b 0
:failed
echo Setup stopped. Review the error above; no application data was deleted.
pause
exit /b 1
