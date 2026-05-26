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
    echo         Chay lenh: python -m venv venv
    echo         Sau do:    venv\Scripts\activate
    echo         Sau do:    pip install -r requirements.txt
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
    echo       PyInstaller not found, installing...
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
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
echo       OK

:: ── Kiểm tra assets ──────────────────────────────────────────────
echo [4/6] Checking assets...
if not exist "assets\icon.ico" (
    echo [WARN] assets\icon.ico not found - app will have no icon
)
if not exist "assets\icon.png" (
    echo [WARN] assets\icon.png not found
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
    --icon "assets\icon.ico" ^
    --add-data "assets;assets" ^
    --add-data "ui;ui" ^
    --add-data "cache;cache" ^
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
    main.py

:: ── Kiểm tra kết quả ─────────────────────────────────────────────
echo.
echo [6/6] Checking output...

if not exist "dist\TranslatorTdev\TranslatorTdev.exe" (
    echo.
    echo [ERROR] BUILD FAILED!
    echo         Kiem tra log o tren de xem loi.
    pause
    exit /b 1
)

:: ── Copy settings mặc định vào dist ──────────────────────────────
echo       Copying default settings...
if exist "settings.json" (
    copy /y "settings.json" "dist\TranslatorTdev\settings.json" >nul
)

:: ── Tạo thư mục cache trong dist ─────────────────────────────────
if not exist "dist\TranslatorTdev\cache" (
    mkdir "dist\TranslatorTdev\cache"
    if exist "cache\.gitkeep" (
        copy /y "cache\.gitkeep" "dist\TranslatorTdev\cache\.gitkeep" >nul
    )
)

:: ── Tạo file README trong dist ───────────────────────────────────
echo. > "dist\TranslatorTdev\HOW_TO_RUN.txt"
echo TranslatorTdev v1.0.0 >> "dist\TranslatorTdev\HOW_TO_RUN.txt"
echo ======================== >> "dist\TranslatorTdev\HOW_TO_RUN.txt"
echo. >> "dist\TranslatorTdev\HOW_TO_RUN.txt"
echo 1. Chay file TranslatorTdev.exe >> "dist\TranslatorTdev\HOW_TO_RUN.txt"
echo 2. Lan dau chay se download EasyOCR models (~100MB) >> "dist\TranslatorTdev\HOW_TO_RUN.txt"
echo 3. Nhan phim Q (hoac hotkey da cai) de bat dau dich >> "dist\TranslatorTdev\HOW_TO_RUN.txt"
echo 4. Keo chon vung man hinh chua chu >> "dist\TranslatorTdev\HOW_TO_RUN.txt"
echo 5. Nhan ENTER de dich >> "dist\TranslatorTdev\HOW_TO_RUN.txt"
echo. >> "dist\TranslatorTdev\HOW_TO_RUN.txt"
echo Mac dinh dung Google Translate (mien phi, can internet) >> "dist\TranslatorTdev\HOW_TO_RUN.txt"
echo Co the doi sang Ollama/LM Studio de dich offline. >> "dist\TranslatorTdev\HOW_TO_RUN.txt"

:: ── Thống kê ─────────────────────────────────────────────────────
echo.
echo ========================================
echo   BUILD SUCCESS!
echo ========================================
echo.
echo   Output: dist\TranslatorTdev\
echo.

:: Tính size thư mục dist
for /f "tokens=3" %%a in ('dir /s /a "dist\TranslatorTdev" ^| find "File(s)"') do (
    echo   Size: %%a bytes
)

echo.
echo   Next steps:
echo   1. Test chay thu: dist\TranslatorTdev\TranslatorTdev.exe
echo   2. Nen lai:       chuot phai dist\TranslatorTdev ^> Send to ^> Compressed folder
echo   3. Upload len:    GitHub Releases
echo.
echo ========================================
pause