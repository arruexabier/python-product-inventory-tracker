@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python environment...
    py -m venv .venv || goto :error
)
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt || goto :error
python main.py run %* || goto :error
pause
exit /b 0

:error
echo.
echo The tracker could not complete. Check the error shown above.
pause
exit /b 1
