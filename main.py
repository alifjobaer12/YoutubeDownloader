import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import yt_dlp
import os
import time

# Appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# App setup
app = ctk.CTk()
app.geometry("700x490")
app.title("🎬 YouTube Downloader")

download_path = os.getcwd()
start_time = 0

# Control flags
download_thread = None
pause_flag = False

# Format helpers
def format_bytes(size):
    return f"{size / 1024 / 1024:.2f} MB" if size else "Unknown"

def format_eta(seconds):
    if not seconds or seconds <= 0:
        return "Calculating..."
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"

# Folder picker
def choose_folder():
    global download_path
    folder = filedialog.askdirectory()
    if folder:
        download_path = folder
        folder_label.configure(text=download_path)

# yt-dlp progress hook
def progress_hook(d):
    global pause_flag
    if pause_flag:
        # Raise an exception to stop the download
        raise yt_dlp.utils.DownloadError("Download paused by user.")
    
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        eta = d.get('eta', 0)

        if total:
            percent = int(downloaded / total * 100)
            progress_bar.set(percent / 100)
            percent_label.configure(text=f"{percent}%")
            mb_info = f"{format_bytes(downloaded)} / {format_bytes(total)}"
            status_label.configure(text=f"🟠 Downloading...\n{mb_info} \t\t ETA: {format_eta(eta)}", text_color="orange")

    elif d['status'] == 'finished':
        progress_bar.set(1.0)
        percent_label.configure(text="100%")
        status_label.configure(text="✅ Download complete!", text_color="green")

# Download logic
def start_download(resume=False):
    global start_time, pause_flag
    pause_flag = False
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("Missing URL", "Please enter a YouTube URL.")
        return

    try:
        progress_bar.set(0)
        percent_label.configure(text="0%")
        status_label.configure(text="Fetching video info...", text_color="orange")
        video_title.configure(text="")

        ydl_opts = {
            'format': 'bestaudio/best' if mode_option.get() == "Audio" else 'bv*+ba/bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'quiet': True,
            'noplaylist': True,
            'progress_hooks': [progress_hook],
            'continuedl': True,  # enable resume download if file exists
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown Title')
            height = info.get('height', 'N/A')
            video_title.configure(text=f"{title} ({height}p)", text_color="#00ffff")

            status_label.configure(text="Starting download...", text_color="orange")
            start_time = time.time()
            ydl.download([url])

        status_label.configure(text="✅ Download complete!", text_color="green")

    except yt_dlp.utils.DownloadError as e:
        if str(e) == "Download paused by user.":
            status_label.configure(text="⏸ Download paused.", text_color="yellow")
        else:
            status_label.configure(text="❌ Download failed!", text_color="red")
            messagebox.showerror("Error", f"An error occurred:\n{e}")

    except Exception as e:
        status_label.configure(text="❌ Download failed!", text_color="red")
        messagebox.showerror("Error", f"An error occurred:\n{e}")

def threaded_download():
    global download_thread, pause_flag
    pause_flag = False
    download_thread = threading.Thread(target=start_download, daemon=True)
    download_thread.start()

def pause_resume():
    global pause_flag, download_thread
    if download_thread and download_thread.is_alive():
        # Pause
        pause_flag = True
        pause_btn.configure(text="▶️ Resume")
    else:
        # Resume
        pause_flag = False
        pause_btn.configure(text="⏸ Pause")
        threaded_download()

# UI Layout
title_label = ctk.CTkLabel(app, text="📥 YouTube Downloader", font=ctk.CTkFont(size=24, weight="bold"), text_color="skyblue")
title_label.pack(pady=20)

url_entry = ctk.CTkEntry(app, width=520, height=40, placeholder_text="🔗 Paste YouTube URL here...")
url_entry.pack(pady=10)

mode_option = ctk.CTkOptionMenu(app, values=["Video", "Audio"])
mode_option.set("Video")
mode_option.pack(pady=(10, 20))

folder_label = ctk.CTkLabel(app, text=download_path, font=ctk.CTkFont(size=12), text_color="gray")
folder_label.pack(pady=2)

folder_btn = ctk.CTkButton(app, text="📁", font=("arial", 20, "bold"), height=10, width=10, fg_color="#3b82f6", hover_color="#2563eb", command=choose_folder)
folder_btn.pack(pady=(5, 20))

button_frame = ctk.CTkFrame(app)
button_frame.pack(pady=10)

download_btn = ctk.CTkButton(button_frame, text="⬇️ Start Download", font=("arial", 18, "bold"), width=160, height=40, fg_color="#10b981", hover_color="#059669", command=threaded_download)
download_btn.grid(row=0, column=0, padx=10)

pause_btn = ctk.CTkButton(button_frame, text="⏸ Pause", font=("arial", 18, "bold"), width=160, height=40, fg_color="#f59e0b", hover_color="#b45309", command=pause_resume)
pause_btn.grid(row=0, column=1, padx=10)

video_title = ctk.CTkLabel(app, text="", font=ctk.CTkFont(size=16, weight="bold"))
video_title.pack(pady=(10,5))

progress_bar = ctk.CTkProgressBar(app, width=400)
progress_bar.set(0)
progress_bar.pack(pady=8)

percent_label = ctk.CTkLabel(app, text="0%", font=ctk.CTkFont(size=14))
percent_label.pack()

status_label = ctk.CTkLabel(app, text="", font=ctk.CTkFont(size=14))
status_label.pack(pady=10)

# Launch app
app.mainloop()
