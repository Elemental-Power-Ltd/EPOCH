@echo off
SETLOCAL

REM check that administrator permissions are avilable.
net session >nul 2>&1
if %errorLevel% NEQ 0 (
	echo Administrator permissions are required to run this script - please re-run.
	pause
	exit /b 1
)


REM Define the location where you want to clone vcpkg
REM vcpkg can occasionally encounter issues with long files paths so we choose to use a short root directory here
SET vcpkgDir=C:\dev\vcpkg


REM Warn the user if VCPKG_ROOT has already been set
if defined VCPKG_ROOT (
	echo VCPKG_ROOT is already set to "%VCPKG_ROOT%"
	echo Running this script will overwrite this value
	CHOICE /C YN /M "Do you wish to continue?"
	
	IF %ERRORLEVEL% EQU 2 (
		echo Exited without installing vcpkg
		pause
		exit /b 1
	)
	
	REM If the user selects Y the error level will be 1, we need to reset it to 0 before we continue
	ver > nul
)

REM Clone vcpkg
IF NOT EXIST "%vcpkgDir%" (
    echo Cloning vcpkg...
    git clone https://github.com/microsoft/vcpkg.git "%vcpkgDir%" --verbose
	
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to clone vcpkg.
		pause
        exit /b 1
    )
) ELSE (
    echo vcpkg directory already exists.
)


REM Navigate into the vcpkg directory
cd /d "%vcpkgDir%"

REM Bootstrap vcpkg
echo Bootstrapping vcpkg...
call bootstrap-vcpkg.bat
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to bootstrap vcpkg.
	pause
    exit /b 1
)

REM Run vcpkg integrate install
echo Running vcpkg integrate install...
vcpkg integrate install
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to integrate vcpkg.
	pause
    exit /b 1
)

echo Setting VCPKG_ROOT
setx VCPKG_ROOT %vcpkgDir% /M


echo vcpkg set up successfully.
ENDLOCAL
pause