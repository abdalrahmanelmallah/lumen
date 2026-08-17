@echo off
REM Build for Windows.bat
REM
REM Double-click this file in File Explorer to build the Windows Lumen
REM app (a windowed code editor with a Run button). It does everything
REM build.ps1 does for the CLI build, but produces the full GUI app via
REM Lumen.spec, and you never have to open a terminal or type a command.
REM
REM (If Windows SmartScreen warns that this is from an "unknown publisher",
REM that's expected for an unsigned .bat file — click "More info" then
REM "Run anyway".)

cd /d "%~dp0"

echo ==================================================
echo  Building Lumen for Windows...
echo ==================================================
echo.

where python >nul 2>nul
if %errorlevel%==0 (
    set PYTHON=python
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        set PYTHON=py
    ) else (
        echo Python was not found on this machine.
        echo Install it from https://www.python.org/downloads/
        echo IMPORTANT: check "Add python.exe to PATH" during setup, then run this again.
        echo.
        pause
        exit /b 1
    )
)

echo Using: 
%PYTHON% --version
echo.

%PYTHON% -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo.
    echo !! pip install failed - see the error above. !!
    echo.
    pause
    exit /b 1
)

echo.
echo Running PyInstaller (this is the part that can take a minute)...
echo.
%PYTHON% -m PyInstaller --noconfirm Lumen.spec
if errorlevel 1 (
    echo.
    echo !! Build failed - see the error above. !!
    echo.
    pause
    exit /b 1
)

echo.
echo ==================================================
echo  Done!
echo.
echo  Your Windows app is ready at:
echo    %cd%\dist\Lumen\Lumen.exe
echo.
echo  Double-click Lumen.exe to open the editor, or right-click it to
echo  create a Desktop/Start Menu shortcut. To make double-clicking a
echo  .lu file open it in Lumen, right-click any .lu file -^>
echo  Open with -^> Choose another app -^> More apps -^> look for Lumen
echo  (or Browse... to Lumen.exe directly) -^> check "Always use this app".
echo ==================================================
echo.
pause
