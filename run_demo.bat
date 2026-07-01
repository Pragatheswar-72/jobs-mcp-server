@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo.
echo Running the Jobs MCP Server demo...
echo This calls every tool (search, get details, list skills, match) using real data.
echo.
python client_demo.py
echo.
echo Done. Press any key to close this window.
pause >nul
