@echo off
setlocal
cd /d "%~dp0"
echo AlloyForge setup - Python 3.11+ and Node.js LTS are required.
set "PYTHON=python"
python -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>&1
if not errorlevel 1 goto python_ready
set "PYTHON=py -3"
py -3 -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>&1
if errorlevel 1 goto missing_python
:python_ready
node -e "const [a,b]=process.versions.node.split('.').map(Number); process.exit(((a===20 && b>=19)||(a===22 && b>=12)||a>22) ? 0 : 1)" >nul 2>&1
if errorlevel 1 goto missing_node
call npm.cmd --version >nul 2>&1
if errorlevel 1 goto missing_node
if /i "%~1"=="--check" (
  echo Prerequisite check passed. No packages were installed.
  exit /b 0
)
echo [1/4] Creating the local Python environment...
if not exist ".venv\Scripts\python.exe" %PYTHON% -m venv .venv
if errorlevel 1 goto failed
echo [2/4] Updating pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
echo [3/4] Installing Python dependencies, including test tools...
".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if errorlevel 1 goto failed
echo [4/4] Installing browser interface dependencies...
call npm.cmd --prefix frontend install
if errorlevel 1 goto failed
echo Setup complete. Double-click start.bat to open the demo.
exit /b 0
:missing_python
echo ERROR: Install Python 3.11+ from https://www.python.org/downloads/
echo Tick Add Python to PATH, then reopen this window and try again.
goto failed
:missing_node
echo ERROR: Install Node.js LTS from https://nodejs.org/ then try again.
echo Supported: Node 20.19+, 22.12+, or newer LTS.
:failed
echo Setup stopped. Read the error above, fix it, and run setup.bat again.
if /i not "%~1"=="--check" pause
exit /b 1
