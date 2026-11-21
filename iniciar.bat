@echo off
title YouTube Downloader

:: Agregar ffmpeg local al PATH si existe
if exist "%~dp0ffmpeg\ffmpeg.exe" (
    set "PATH=%~dp0ffmpeg;%PATH%"
)

echo  Abriendo YouTube Downloader...
echo  (Se abrira en tu navegador automaticamente)
echo  Presiona Ctrl+C para cerrar.
echo.
python "%~dp0app.py"
