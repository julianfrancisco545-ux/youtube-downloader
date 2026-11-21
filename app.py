#!/usr/bin/env python3
"""
YouTube Downloader — Aplicación web con interfaz gráfica.
Ejecuta este archivo y abre http://localhost:5000 en tu navegador.
"""

import os
import sys
import json
import threading
import webbrowser
import time
import re
import uuid
from pathlib import Path

try:
    from flask import Flask, render_template, request, jsonify, send_file
except ImportError:
    print("Instalando Flask...")
    os.system(f"{sys.executable} -m pip install flask")
    from flask import Flask, render_template, request, jsonify, send_file

try:
    import yt_dlp
except ImportError:
    print("Instalando yt-dlp...")
    os.system(f"{sys.executable} -m pip install yt-dlp")
    import yt_dlp


app = Flask(__name__)

# ── Agregar ffmpeg local al PATH si existe junto a app.py ──
FFMPEG_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg")
if os.path.isdir(FFMPEG_LOCAL):
    os.environ["PATH"] = FFMPEG_LOCAL + os.pathsep + os.environ.get("PATH", "")

# ── Detectar si ffmpeg está disponible ──
import shutil
HAS_FFMPEG = shutil.which("ffmpeg") is not None

# Estado global de descargas
downloads = {}
DEFAULT_FOLDER = str(Path.home() / "Downloads")


def get_video_info(url):
    """Obtiene información del video sin descargarlo."""
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Sin título"),
            "channel": info.get("channel", "Desconocido"),
            "duration": info.get("duration_string", "N/A"),
            "thumbnail": info.get("thumbnail", ""),
            "view_count": info.get("view_count", 0),
            "upload_date": info.get("upload_date", ""),
        }


def download_video(download_id, url, folder, quality, custom_filename=""):
    """Descarga el video en un hilo separado."""
    downloads[download_id]["status"] = "downloading"
    downloads[download_id]["progress"] = 0

    os.makedirs(folder, exist_ok=True)

    # Formato según calidad elegida
    # Si NO hay ffmpeg, usar formatos que ya vienen con video+audio en un solo archivo
    if HAS_FFMPEG:
        if quality == "best":
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        elif quality == "720":
            fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"
        elif quality == "480":
            fmt = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best"
        elif quality == "360":
            fmt = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best"
        elif quality == "audio":
            fmt = "bestaudio[ext=m4a]/bestaudio"
        else:
            fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    else:
        # Sin ffmpeg: solo formatos pre-merged (video+audio en un archivo)
        if quality == "best":
            fmt = "best[ext=mp4]/best"
        elif quality == "720":
            fmt = "best[height<=720][ext=mp4]/best[height<=720]/best"
        elif quality == "480":
            fmt = "best[height<=480][ext=mp4]/best[height<=480]/best"
        elif quality == "360":
            fmt = "best[height<=360][ext=mp4]/best[height<=360]/best"
        elif quality == "audio":
            fmt = "bestaudio[ext=m4a]/bestaudio/best"
        else:
            fmt = "best[ext=mp4]/best"

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                downloads[download_id]["progress"] = round((downloaded / total) * 100, 1)
            downloads[download_id]["speed"] = d.get("_speed_str", "")
            downloads[download_id]["eta"] = d.get("_eta_str", "")
        elif d["status"] == "finished":
            downloads[download_id]["progress"] = 100
            downloads[download_id]["status"] = "processing"

    opts = {
        "format": fmt,
        "outtmpl": os.path.join(folder, (custom_filename + ".%(ext)s") if custom_filename else "%(title)s.%(ext)s"),
        "progress_hooks": [hook],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    # Solo pedir merge si ffmpeg está disponible
    if HAS_FFMPEG:
        opts["merge_output_format"] = "mp4" if quality != "audio" else "m4a"

    # Si es solo audio, extraer a m4a
    if quality == "audio":
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
        }]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            ext = "m4a" if quality == "audio" else "mp4"
            filename = os.path.splitext(filename)[0] + f".{ext}"

            downloads[download_id]["status"] = "complete"
            downloads[download_id]["progress"] = 100
            downloads[download_id]["file"] = filename
    except Exception as e:
        downloads[download_id]["status"] = "error"
        downloads[download_id]["error"] = str(e)


# ─── Rutas ───

@app.route("/")
def index():
    return render_template("index.html", default_folder=DEFAULT_FOLDER, has_ffmpeg=HAS_FFMPEG)


@app.route("/api/info", methods=["POST"])
def api_info():
    """Obtiene info del video antes de descargar."""
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No se proporcionó URL"}), 400
    try:
        info = get_video_info(url)
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/browse-folder", methods=["POST"])
def api_browse_folder():
    """Abre un diálogo para elegir carpeta (usa tkinter)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title="Elige dónde guardar los videos")
        root.destroy()
        if folder:
            return jsonify({"folder": folder})
        return jsonify({"folder": ""})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def api_download():
    """Inicia la descarga de un video."""
    data = request.json
    url = data.get("url", "").strip()
    folder = data.get("folder", DEFAULT_FOLDER).strip() or DEFAULT_FOLDER
    quality = data.get("quality", "best")
    custom_filename = data.get("filename", "").strip()

    if not url:
        return jsonify({"error": "No se proporcionó URL"}), 400

    download_id = str(uuid.uuid4())[:8]
    downloads[download_id] = {
        "url": url,
        "status": "starting",
        "progress": 0,
        "speed": "",
        "eta": "",
        "file": "",
        "error": "",
    }

    thread = threading.Thread(
        target=download_video,
        args=(download_id, url, folder, quality, custom_filename),
        daemon=True,
    )
    thread.start()

    return jsonify({"id": download_id})


@app.route("/api/status/<download_id>")
def api_status(download_id):
    """Consulta el estado de una descarga."""
    if download_id not in downloads:
        return jsonify({"error": "Descarga no encontrada"}), 404
    return jsonify(downloads[download_id])


@app.route("/api/open-folder", methods=["POST"])
def api_open_folder():
    """Abre la carpeta de descargas en el explorador de archivos."""
    data = request.json
    folder = data.get("folder", DEFAULT_FOLDER)
    try:
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            os.system(f'open "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║   📥 YouTube Downloader                      ║")
    print("  ║   Abre tu navegador en: http://localhost:5000 ║")
    print("  ║   Presiona Ctrl+C para cerrar                ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()

    # Abrir navegador automáticamente después de 1.5 seg
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5000")).start()

    app.run(host="0.0.0.0", port=5000, debug=False)
