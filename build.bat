@echo off
setlocal
cd /d "%~dp0"
py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --clean --windowed --onefile --name LiteDock main.py
echo.
echo Build finished. Output: dist\LiteDock.exe
pause
