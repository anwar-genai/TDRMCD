@echo off
setlocal ENABLEDELAYEDEXPANSION

REM -----------------------------------------------------------------
REM TDRMCD Release Packager (Windows)
REM Creates a clean ZIP without .git/venv and with needed folders.
REM Output: dist\tdrmcd-release-YYYYMMDD-HHMMSS.zip
REM -----------------------------------------------------------------

for /f "tokens=1-5 delims=/:. " %%a in ("%date% %time%") do (
  set YYYY=%%c
  set MM=%%a
  set DD=%%b
  set HH=%%d
  set MN=%%e
)
set TS=%YYYY%%MM%%DD%-%HH%%MN%

set ROOT=%~dp0
set DIST=%ROOT%dist
set STAGE=%DIST%\tdrmcd_release
set ZIP=%DIST%\tdrmcd-release-%TS%.zip

echo ================================================================
echo Building TDRMCD release package...
echo Staging: %STAGE%
echo Output : %ZIP%
echo ================================================================

if not exist "%DIST%" mkdir "%DIST%"
if exist "%STAGE%" rmdir /S /Q "%STAGE%"
mkdir "%STAGE%"

REM Copy top-level files
copy /Y "%ROOT%app.py" "%STAGE%\" >nul 2>&1
copy /Y "%ROOT%run.py" "%STAGE%\" >nul 2>&1
copy /Y "%ROOT%config.py" "%STAGE%\" >nul 2>&1
copy /Y "%ROOT%forms.py" "%STAGE%\" >nul 2>&1
copy /Y "%ROOT%models.py" "%STAGE%\" >nul 2>&1
copy /Y "%ROOT%requirements.txt" "%STAGE%\" >nul 2>&1
copy /Y "%ROOT%README.md" "%STAGE%\" >nul 2>&1
copy /Y "%ROOT%ENV_CONFIGURATION.md" "%STAGE%\" >nul 2>&1
copy /Y "%ROOT%env.template" "%STAGE%\" >nul 2>&1
copy /Y "%ROOT%setup.bat" "%STAGE%\" >nul 2>&1
copy /Y "%ROOT%start_app.bat" "%STAGE%\" >nul 2>&1

REM Copy key directories using robocopy (excludes __pycache__)
robocopy "%ROOT%routes" "%STAGE%\routes" /E /NFL /NDL /NJH /NJS /XD __pycache__ >nul
robocopy "%ROOT%templates" "%STAGE%\templates" /E /NFL /NDL /NJH /NJS /XD __pycache__ >nul
robocopy "%ROOT%static" "%STAGE%\static" /E /NFL /NDL /NJH /NJS /XD __pycache__ >nul
robocopy "%ROOT%migrations" "%STAGE%\migrations" /E /NFL /NDL /NJH /NJS /XD __pycache__ >nul

REM Ensure instance folder exists (db will be created on first run)
mkdir "%STAGE%\instance" >nul 2>&1

REM Create empty uploads structure for runtime-served files
mkdir "%STAGE%\uploads" >nul 2>&1
mkdir "%STAGE%\uploads\avatars" >nul 2>&1
mkdir "%STAGE%\uploads\resources" >nul 2>&1
mkdir "%STAGE%\uploads\posts" >nul 2>&1
mkdir "%STAGE%\uploads\campaigns" >nul 2>&1
mkdir "%STAGE%\uploads\submissions" >nul 2>&1

REM Remove any cached Python files from stage just in case
for /r "%STAGE%" %%F in (*.pyc) do del /q "%%F" >nul 2>&1

REM Build zip using PowerShell
powershell -NoLogo -NoProfile -Command "Compress-Archive -Path '%STAGE%\*' -DestinationPath '%ZIP%' -Force" 1>nul
if %errorlevel% neq 0 (
  echo Failed to create zip. Ensure PowerShell is available.
  exit /b 1
)

echo.
echo ✓ Release created: %ZIP%
echo.
echo Include instructions to client:
echo   1) Unzip anywhere with write permissions
echo   2) Double-click setup.bat (creates venv, installs deps, writes .env)
echo   3) Double-click start_app.bat (starts app)
echo.
echo Default admin: admin / admin123
echo ================================================================
exit /b 0


