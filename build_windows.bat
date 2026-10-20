@echo off
chcp 65001 >nul
echo ============================================
echo  SLT Upper Computer - Build Windows EXE
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.8+ and check "Add to PATH".
    pause
    exit /b 1
)

:: Show which python
echo Using Python:
python --version
echo.

:: Install dependencies (use python -m pip to avoid PATH issues)
echo [1/3] Installing dependencies...
python -m pip install PyQt5 pyserial pyinstaller -q
if errorlevel 1 (
    echo.
    echo [ERROR] pip install failed! Try: python -m pip install --upgrade pip
    pause
    exit /b 1
)

:: Clean old build
echo [2/3] Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist run.spec del /q run.spec

:: Build (use python -m PyInstaller to avoid PATH issues)
echo [3/3] Building EXE (this may take 1-2 minutes)...
python -m PyInstaller ^
    --noconfirm ^
    --windowed ^
    --onefile ^
    --name "SLT_Test_Tool" ^
    --add-data "ui;ui" ^
    --collect-submodules PyQt5 ^
    run.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed! Scroll up to see the error.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  DONE! EXE is at: dist\SLT_Test_Tool.exe
echo ============================================
echo.
pause
