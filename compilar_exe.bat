@echo off
title Compilador a EXE - TijeralCAD Pro
echo ======================================================================
echo    Compilando TijeralCAD Pro a ejecutable standalone (.exe)
echo ======================================================================
echo.

py -m PyInstaller --noconsole --onefile --name "TijeralCAD_Pro" --collect-all reportlab --hidden-import="PySide6.QtCore" --hidden-import="PySide6.QtGui" --hidden-import="PySide6.QtWidgets" --hidden-import="matplotlib.backends.backend_qtagg" --hidden-import="ezdxf" app_tijeral.py
copy /Y dist\TijeralCAD_Pro.exe TijeralCAD_Pro.exe

echo.
echo ======================================================================
echo    Compilacion terminada. El archivo ejecutable esta en la carpeta dist/
echo ======================================================================
pause
