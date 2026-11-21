@echo off
title Instalando YouTube Downloader
echo.
echo  ========================================
echo    Instalando YouTube Downloader...
echo  ========================================
echo.

:: ── Verificar Python ──
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python no esta instalado.
    echo  Descargalo de https://www.python.org/downloads/
    echo  IMPORTANTE: Marca "Add Python to PATH" al instalar.
    echo.
    pause
    exit /b
)
echo  [OK] Python encontrado.

:: ── Instalar dependencias de Python ──
echo  Instalando yt-dlp y Flask...
pip install yt-dlp flask >nul 2>&1
echo  [OK] yt-dlp y Flask instalados.

:: ── Verificar si ffmpeg ya esta instalado ──
ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] ffmpeg ya esta instalado.
    goto :done
)

echo.
echo  ffmpeg no esta instalado. Descargando...
echo  (Esto puede tomar unos minutos)
echo.

:: ── Crear carpeta ffmpeg ──
if not exist "%~dp0ffmpeg" mkdir "%~dp0ffmpeg"

:: ── Descargar ffmpeg con PowerShell ──
echo  Descargando ffmpeg...
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'; $out = '%~dp0ffmpeg\ffmpeg.zip'; Write-Host '  Descargando desde gyan.dev...'; Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing; Write-Host '  Descarga completa.' }"

if not exist "%~dp0ffmpeg\ffmpeg.zip" (
    echo.
    echo  [ERROR] No se pudo descargar ffmpeg.
    echo  Descargalo manualmente de https://www.gyan.dev/ffmpeg/builds/
    echo  y coloca ffmpeg.exe en la carpeta "ffmpeg" junto a app.py
    pause
    exit /b
)

:: ── Extraer ffmpeg ──
echo  Extrayendo ffmpeg...
powershell -Command "& { Expand-Archive -Path '%~dp0ffmpeg\ffmpeg.zip' -DestinationPath '%~dp0ffmpeg\temp' -Force }"

:: ── Mover los .exe a la carpeta ffmpeg ──
for /d %%D in ("%~dp0ffmpeg\temp\ffmpeg-*") do (
    if exist "%%D\bin\ffmpeg.exe" (
        copy /Y "%%D\bin\ffmpeg.exe" "%~dp0ffmpeg\" >nul
        copy /Y "%%D\bin\ffprobe.exe" "%~dp0ffmpeg\" >nul
    )
)

:: ── Limpiar archivos temporales ──
if exist "%~dp0ffmpeg\temp" rmdir /s /q "%~dp0ffmpeg\temp"
if exist "%~dp0ffmpeg\ffmpeg.zip" del "%~dp0ffmpeg\ffmpeg.zip"

:: ── Verificar que se extrajo bien ──
if exist "%~dp0ffmpeg\ffmpeg.exe" (
    echo  [OK] ffmpeg instalado correctamente.
) else (
    echo  [ERROR] No se pudo extraer ffmpeg.
    echo  Descargalo manualmente de https://www.gyan.dev/ffmpeg/builds/
    pause
    exit /b
)

:done
echo.
echo  ========================================
echo    Instalacion completa!
echo    Ejecuta "iniciar.bat" para abrir la app.
echo  ========================================
echo.
pause
