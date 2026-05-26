@echo off
chcp 65001 >nul
title TranslatorTdev Builder

:: Tự động cd về thư mục chứa file .bat
cd /d "%~dp0"

echo.
echo ========================================
echo   TranslatorTdev v1.0.0 - Builder
echo ========================================
echo.

:: Kiểm tra venv
if not exist "%~dp0venv\Scripts\python.exe" (
    echo [ERROR] Khong tim thay venv!
    echo         Chay lenh: python -m venv venv
    pause
    exit /b 1
)

:: Dùng python từ venv trực tiếp, không cần activate
set PYTHON=%~dp0venv\Scripts\python.exe
set PIP=%~dp0venv\Scripts\pip.exe

echo [INFO] Python: %PYTHON%
echo.

:: Kiểm tra PyInstaller
%PYTHON% -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [2/6] PyInstaller not found, installing...
    %PIP% install pyinstaller
    if errorlevel 1 (
        echo [ERROR] PyInstaller install failed!
        pause
        exit /b 1
    )
) else (
    echo [2/6] PyInstaller OK
)

:: Dọn build cũ
echo [3/6] Cleaning old build...
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
echo       OK

:: Kiểm tra assets
echo [4/6] Checking assets...
if not exist "assets\icon.ico" (
    echo [WARN] assets\icon.ico not found
)
echo       OK

:: Build
echo [5/6] Building...
echo.

%PYTHON% -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --name "TranslatorTdev" ^
    --windowed ^
    --icon "%~dp0assets\icon.ico" ^
    --add-data "%~dp0assets;assets" ^
    --add-data "%~dp0ui;ui" ^
    --add-data "%~dp0cache;cache" ^
    --hidden-import "easyocr" ^
    --hidden-import "torch" ^
    --hidden-import "torchvision" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "PIL.ImageEnhance" ^
    --hidden-import "mss" ^
    --hidden-import "mss.tools" ^
    --hidden-import "pynput" ^
    --hidden-import "pynput.keyboard" ^
    --hidden-import "pynput._util.win32" ^
    --hidden-import "deep_translator" ^
    --hidden-import "deep_translator.google" ^
    --hidden-import "PySide6" ^
    --hidden-import "PySide6.QtWidgets" ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "numpy" ^
    --hidden-import "requests" ^
    --hidden-import "openai" ^
    --hidden-import "shapely" ^
    --hidden-import "skimage" ^
    --hidden-import "scipy" ^
    --hidden-import "yaml" ^
    --hidden-import "cv2" ^
    --exclude-module "matplotlib" ^
    --exclude-module "notebook" ^
    --exclude-module "ipython" ^
    --exclude-module "pandas" ^
    --exclude-module "tkinter" ^
    --exclude-module "PyQt5" ^
    --exclude-module "PyQt6" ^
    "%~dp0main.py"

:: Kiểm tra kết quả
echo.
echo [6/6] Checking output...

if not exist "dist\TranslatorTdev\TranslatorTdev.exe" (
    echo.
    echo [ERROR] BUILD FAILED!
    pause
    exit /b 1
)

:: Copy files cần thiết
echo       Copying default settings...
if exist "settings.json" (
    copy /y "settings.json" "dist\TranslatorTdev\settings.json" >nul
)

if not exist "dist\TranslatorTdev\cache" (
    mkdir "dist\TranslatorTdev\cache"
)

if exist "assets\icon.ico" (
    copy /y "assets\icon.ico" "dist\TranslatorTdev\icon.ico" >nul
)

echo.
echo ========================================
echo   BUILD SUCCESS!
echo ========================================
echo   Output: dist\TranslatorTdev\
echo ========================================
pause