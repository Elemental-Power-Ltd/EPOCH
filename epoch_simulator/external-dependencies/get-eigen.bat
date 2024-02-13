@echo off
setlocal

:: This is a convenience script to download eigen and extract it


set "URL=https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.zip"


:: download using curl
curl -O %URL%

:: extract using tar
tar -xf eigen-3.4.0.zip

:: remove the zip
del eigen-3.4.0.zip

endlocal