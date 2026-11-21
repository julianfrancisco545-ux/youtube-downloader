# YouTube Downloader

Aplicación web local (Flask + yt-dlp) para descargar videos o audio de YouTube con una interfaz gráfica en el navegador.

## Requisitos
- Python 3 (marca "Add Python to PATH" al instalar)
- ffmpeg (opcional, para mejor calidad y audio; `instalar.bat` lo descarga automáticamente)

## Instalación (Windows)
1. Ejecuta `instalar.bat`
2. Ejecuta `iniciar.bat`
3. Se abrirá http://localhost:5000 en tu navegador

## Instalación manual
```
pip install -r requirements.txt
python app.py
```

## Calidades disponibles
Mejor calidad, 720p, 480p, 360p y solo audio (m4a).
