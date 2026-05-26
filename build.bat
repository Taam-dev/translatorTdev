@echo off
chcp 65001 >nul
title TranslatorTdev Builder

echo.
echo ========================================
echo   TranslatorTdev v1.0.0 - Builder
echo ========================================
echo.

:: ── Kiểm tra venv ────────────────────────────────────────────────
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Khong tim thay venv!
    echo         Chay: python -m venv venv
    echo         Sau:  venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

:: ── Activate venv ────────────────────────────────────────────────
echo [1/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo       OK

:: ── Kiểm tra PyInstaller ─────────────────────────────────────────
echo [2/6] Checking PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo       Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] PyInstaller install failed!
        pause
        exit /b 1
    )
)
echo       OK

:: ── Dọn build cũ ─────────────────────────────────────────────────
echo [3/6] Cleaning old build...
if exist "build"              rmdir /s /q "build"
if exist "dist"               rmdir /s /q "dist"
if exist "TranslatorTdev.spec" del /q "TranslatorTdev.spec"
echo       OK

:: ── Kiểm tra / generate assets ───────────────────────────────────
echo [4/6] Checking assets...
if not exist "assets" mkdir assets

if not exist "assets\icon.ico" (
    echo       Generating icon...
    python assets\generate_assets.py
    if errorlevel 1 (
        echo [WARN] Asset generation failed - continuing without icon
    )
)

set ICON_ARG=
if exist "assets\icon.ico" (
    set ICON_ARG=--icon "assets\icon.ico"
    echo       Icon: OK
) else (
    echo [WARN] No icon found - exe will have default icon
)
echo       OK

:: ── Build ────────────────────────────────────────────────────────
echo [5/6] Building executable...
echo.

pyinstaller ^
    --noconfirm ^
    --clean ^
    --name "TranslatorTdev" ^
    --windowed ^
    %ICON_ARG% ^
    --add-data "assets;assets" ^
    --add-data "ui;ui" ^
    --add-data "cache;cache" ^
    --collect-all "easyocr" ^
    --collect-all "deep_translator" ^
    --hidden-import "torch" ^
    --hidden-import "torchvision" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL.Image" ^
    --hidden-import "PIL.ImageEnhance" ^
    --hidden-import "PIL.ImageFilter" ^
    --hidden-import "mss" ^
    --hidden-import "mss.tools" ^
    --hidden-import "pynput" ^
    --hidden-import "pynput.keyboard" ^
    --hidden-import "pynput.mouse" ^
    --hidden-import "pynput._util" ^
    --hidden-import "pynput._util.win32" ^
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
    --hidden-import "urllib3" ^
    --hidden-import "charset_normalizer" ^
    --exclude-module "matplotlib" ^
    --exclude-module "notebook" ^
    --exclude-module "ipython" ^
    --exclude-module "pandas" ^
    --exclude-module "tkinter" ^
    --exclude-module "PyQt5" ^
    --exclude-module "PyQt6" ^
    main.py

:: ── Kiểm tra kết quả build ───────────────────────────────────────
echo.
if not exist "dist\TranslatorTdev\TranslatorTdev.exe" (
    echo [ERROR] BUILD FAILED!
    echo         Xem log phia tren de tim loi.
    pause
    exit /b 1
)

:: ── Post-build setup ─────────────────────────────────────────────
echo [6/6] Post-build setup...

:: Copy settings.json vào dist (user settings)
if exist "settings.json" (
    copy /y "settings.json" "dist\TranslatorTdev\settings.json" >nul
    echo       Copied: settings.json
)

:: Tạo thư mục cache
if not exist "dist\TranslatorTdev\cache" (
    mkdir "dist\TranslatorTdev\cache"
)
:: Giữ cache trong dist nếu có
if exist "cache\translation_cache.json" (
    copy /y "cache\translation_cache.json" "dist\TranslatorTdev\cache\translation_cache.json" >nul
    echo       Copied: translation_cache.json
)

:: Tạo HOW_TO_RUN.txt
(
    echo TranslatorTdev v1.0.0
    echo ========================
    echo.
    echo CACH SU DUNG:
    echo 1. Chay TranslatorTdev.exe
    echo 2. Lan dau chay se download EasyOCR models ~100MB ^(chi 1 lan^)
    echo 3. Nhan phim Q de bat dau chon vung man hinh
    echo 4. Keo chon vung chua chu
    echo 5. Nhan ENTER de dich
    echo 6. Click vao overlay de dong ket qua dich
    echo.
    echo TRANSLATION BACKENDS:
    echo - Google Translate: mien phi, can internet
    echo - Ollama: mien phi, offline, chat luong cao
    echo   Download: https://ollama.ai
    echo   Model:    ollama pull qwen2.5:7b
    echo - LM Studio: mien phi, offline
    echo   Download: https://lmstudio.ai
    echo.
    echo DEBUG:
    echo - Neu co loi, xem file: translatorTdev.log
    echo   ^(file nay tu dong tao khi chay exe^)
    echo.
    echo PHIM TAT:
    echo - Q          : Chup man hinh
    echo - ESC        : Huy chon
    echo - ENTER      : Xac nhan chon va dich
    echo - Click overlay: Dong ket qua dich
) > "dist\TranslatorTdev\HOW_TO_RUN.txt"

echo       Created: HOW_TO_RUN.txt

:: ── Tính size ─────────────────────────────────────────────────────
echo.
echo ========================================
echo   BUILD SUCCESS!
echo ========================================
echo.
echo   Output folder : dist\TranslatorTdev\
echo   Executable    : dist\TranslatorTdev\TranslatorTdev.exe
echo   Debug log     : dist\TranslatorTdev\translatorTdev.log ^(auto-created on run^)
echo.

:: Đếm files và tính size
set file_count=0
for /r "dist\TranslatorTdev" %%f in (*) do set /a file_count+=1
echo   Files: %file_count%

:: Size thư mục
for /f "tokens=3" %%a in ('dir /s /a "dist\TranslatorTdev" 2^>nul ^| find "File(s)"') do (
    echo   Total size: %%a bytes
)

echo.
echo   NEXT STEPS:
echo   1. Test: dist\TranslatorTdev\TranslatorTdev.exe
echo   2. Zip:  chuot phai dist\TranslatorTdev ^> Send to ^> Compressed folder
echo.
echo ========================================
pause