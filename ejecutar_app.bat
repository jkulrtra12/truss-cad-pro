@echo off
title TijeralCAD Pro - Diseno de Tijeral en V Invertida
echo ======================================================================
echo    Iniciando TijeralCAD Pro v2.0 (PySide6 / AISC 360 LRFD)
echo ======================================================================
echo.

py app_tijeral.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion con 'py'.
    echo Intentando con 'python'...
    python app_tijeral.py
)

pause
