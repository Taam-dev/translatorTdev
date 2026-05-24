@echo off
echo ========================================
echo Building TranslatorTdev v1.0.0
echo ========================================

call venv\Scripts\activate

echo Cleaning old build...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo Building executable...
pyinstaller build.spec --clean

echo.
echo ========================================
if exist "dist\TranslatorTdev\TranslatorTdev.exe" (
    echo BUILD SUCCESS!
    echo Output: dist\TranslatorTdev\TranslatorTdev.exe
) else (
    echo BUILD FAILED - check errors above
)
echo ========================================
pause