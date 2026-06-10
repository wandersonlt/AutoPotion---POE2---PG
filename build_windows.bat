@echo off
echo Building License Manager for Windows...

:: Install PyInstaller
pip install pyinstaller

:: Build the application
pyinstaller --onefile --windowed --name "LicenseManager" --icon=icon.ico ^
    --add-data "translations;translations" ^
    --hidden-import=customtkinter ^
    --hidden-import=PIL ^
    frontend/main.py

:: Copy translations
xcopy translations dist\LicenseManager\translations\ /E /I

echo Build complete! Check the 'dist' folder.
pause