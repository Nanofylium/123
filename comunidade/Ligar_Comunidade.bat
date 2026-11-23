@echo off
chcp 65001 >nul
title Comunidade de Wallace Ross
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ligar.ps1"
echo.
pause
