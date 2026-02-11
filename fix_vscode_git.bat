@echo off
setlocal EnableExtensions EnableDelayedExpansion

title VS Code Git Path Fix
echo VS Code Git Path Fix
echo ====================
echo.

rem --- Locate git.exe ---
set "GIT_EXE="

for /f "delims=" %%G in ('where git 2^>nul') do (
	if not defined GIT_EXE set "GIT_EXE=%%~fG"
)

if not defined GIT_EXE (
	for %%P in (
		"%ProgramFiles%\Git\cmd\git.exe"
		"%ProgramFiles%\Git\bin\git.exe"
		"%ProgramFiles(x86)%\Git\cmd\git.exe"
		"%ProgramFiles(x86)%\Git\bin\git.exe"
		"%LocalAppData%\Programs\Git\cmd\git.exe"
		"%LocalAppData%\Programs\Git\bin\git.exe"
		"D:\Git\cmd\git.exe"
		"D:\Git\bin\git.exe"
	) do (
		if not defined GIT_EXE if exist "%%~fP" set "GIT_EXE=%%~fP"
	)
)

if not defined GIT_EXE (
	echo ERROR: Could not find git.exe.
	echo.
	echo Fix:
	echo - Install Git for Windows from https://git-scm.com/download/win
	echo - During install, allow Git to be added to PATH.
	echo - Then re-run this script.
	echo.
	pause
	exit /b 1
)

echo Found Git at:
echo   %GIT_EXE%
echo.

rem --- Ensure .vscode folder exists ---
set "VSCODE_DIR=%~dp0.vscode"
set "SETTINGS_FILE=%VSCODE_DIR%\settings.json"
if not exist "%VSCODE_DIR%" mkdir "%VSCODE_DIR%" >nul 2>nul

rem --- Backup existing settings.json once ---
if exist "%SETTINGS_FILE%" (
	if not exist "%SETTINGS_FILE%.bak" (
		copy /y "%SETTINGS_FILE%" "%SETTINGS_FILE%.bak" >nul
		echo Backed up existing settings to:
		echo   %SETTINGS_FILE%.bak
		echo.
	)
)

rem --- Write minimal settings for Git detection ---
(
	echo {
	echo     "git.path": "%GIT_EXE:\=\\%",
	echo     "git.enabled": true
	echo }
) > "%SETTINGS_FILE%"

echo Updated:
echo   %SETTINGS_FILE%
echo.
echo Next steps:
echo - Fully close and re-open VS Code.
echo - Open this folder in VS Code.
echo - If Git still doesn't show up, run "Git: Show Git Output" in VS Code.
echo.
echo Note: This script does NOT delete VS Code user data.
echo.
pause
exit /b 0
