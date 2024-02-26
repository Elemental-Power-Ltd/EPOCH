@echo off
SETLOCAL

REM Define the location where you want to clone vcpkg
SET vcpkgDir=%CD%\vcpkg

REM Clone vcpkg
IF NOT EXIST "%vcpkgDir%" (
    echo Cloning vcpkg...
    git clone https://github.com/microsoft/vcpkg.git "%vcpkgDir%"
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to clone vcpkg.
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
    exit /b 1
)

REM Run vcpkg integrate install
echo Running vcpkg integrate install...
vcpkg integrate install
IF %ERRORLEVEL% NEQ 0 (
    echo Failed to integrate vcpkg.
    exit /b 1
)

echo vcpkg is set up successfully.
ENDLOCAL

pause