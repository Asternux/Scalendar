@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if exist "课表日历助手.exe" (
    start "" "%CD%\课表日历助手.exe"
    exit /b 0
)

if exist ".venv\Scripts\pythonw.exe" goto check_dependencies

echo 首次运行：正在创建本地 Python 环境……
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m venv ".venv"
goto install_dependencies

:use_python
where python >nul 2>nul
if errorlevel 1 goto python_missing
python -m venv ".venv"

:install_dependencies
if errorlevel 1 goto setup_failed
echo 正在安装所需组件，请稍候……
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto setup_failed
goto launch

:check_dependencies
".venv\Scripts\python.exe" -c "import customtkinter, openai, openpyxl, tkinterdnd2, tzdata" >nul 2>nul
if errorlevel 1 goto install_dependencies

:launch
start "" ".venv\Scripts\pythonw.exe" "%CD%\app.py"
exit /b 0

:python_missing
echo 未检测到 Python。请先安装 Python 3.10 或更高版本，并勾选 Add Python to PATH。
pause
exit /b 1

:setup_failed
echo 初始化失败。请检查网络连接和 Python 安装，然后重新双击本文件。
pause
exit /b 1
