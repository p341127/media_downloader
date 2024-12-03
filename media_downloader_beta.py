import os
import re
import threading
import tkinter
import customtkinter
from CTkMessagebox import CTkMessagebox
import yt_dlp
from PIL import Image, ImageTk
from pathlib import Path
import requests
from io import BytesIO
import sys
import json
import subprocess
import platform
from tkinter import colorchooser


# Function to get the absolute path to resources
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Load settings from a JSON file
# Load settings from a JSON file
def load_settings():
    try:
        with open("settings.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "download_path": str(Path.home() / "Downloads"),
            "download_playlist": False,
            "audio_only": False,
            "auto_convert": False,
            "video_quality": "best",
            "audio_quality": "best",
            "video_format": "mp4",
            "audio_format": "mp3"
        }


# Save settings to a JSON file
def save_settings():
    new_settings = {
        "download_path": download_path.get(),
        "download_playlist": download_playlist.get(),
        "audio_only": audio_only.get(),
        "auto_convert": auto_convert.get(),
        "video_quality": video_quality.get(),
        "audio_quality": audio_quality.get(),
        "video_format": video_format.get(),
        "audio_format": audio_format.get()
    }
    with open("settings.json", "w") as f:
        json.dump(new_settings, f)

# Save other app settings (checkboxes, dropdowns, etc.) on close
def on_close():
    save_settings()
    app.destroy()


# Load settings
settings = load_settings()

# Appearance settings
customtkinter.set_appearance_mode(settings.get("theme", "dark"))
customtkinter.set_default_color_theme(settings.get("color", "blue"))

# Set global font
custom_font = ("Courier New", 14)
corner_radius = 65

# App frame
app = customtkinter.CTk()

# Temp: Variables for screen size and position
screen_width = 875
screen_height = 625
app.geometry(f"{screen_width}x{screen_height}+"
             f"{int(app.winfo_screenwidth() / 2 - screen_width / 2)}+"
             f"{int(app.winfo_screenheight() / 2 - screen_height / 2)}")  # Fixed size and position
#app.minsize(500, 400)  # Minimum size
app.title("4K Media Downloader by David Park - BETA 0.1.2")

app.protocol("WM_DELETE_WINDOW", on_close)  # Save settings on close


# Use resource_path to get the absolute path to the logo
app.iconbitmap(resource_path("media_downloader_logo.ico"))

# Configure main app grid with adjusted weights
app.grid_rowconfigure(0, weight=1)  # Top row (top frames)
app.grid_rowconfigure(1, weight=2)  # Bottom row (bottom frame, higher weight to avoid disappearing)
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)

# Configure bottom frame (higher priority)
bottom_frame = customtkinter.CTkFrame(master=app, corner_radius=corner_radius)
bottom_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
bottom_frame.grid_rowconfigure([0, 1, 2, 3], weight=1)
bottom_frame.grid_columnconfigure([0, 1, 2], weight=1)

# The top frames
top_left_frame = customtkinter.CTkFrame(master=app, corner_radius=corner_radius)
top_left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
top_left_frame.grid_rowconfigure([0, 1, 2, 3, 4, 5, 6, 7, 8], weight=1)
top_left_frame.grid_columnconfigure(0, weight=1)

top_right_frame = customtkinter.CTkFrame(master=app, corner_radius=corner_radius)
top_right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
top_right_frame.grid_rowconfigure([0, 1, 2, 3, 4, 5], weight=1)
top_right_frame.grid_columnconfigure(0, weight=1)


# Variables
download_path = tkinter.StringVar(value=settings.get("download_path", str(Path.home() / "Downloads")))
download_playlist = tkinter.BooleanVar(value=settings.get("download_playlist", False))
#download_all = tkinter.BooleanVar(app, False) # Old variable/name for download_playlist (download entire playlist)
audio_only = tkinter.BooleanVar(value=settings.get("audio_only", False))
auto_convert = tkinter.BooleanVar(value=settings.get("auto_convert", False))

video_quality = customtkinter.StringVar(value=settings.get("video_quality", "best"))
video_format = customtkinter.StringVar(value=settings.get("video_format", "mp4"))
audio_quality = customtkinter.StringVar(value=settings.get("audio_quality", "best"))
audio_format = customtkinter.StringVar(value=settings.get("audio_format", "mp3"))


thumbnail_image = None
playlist_progress = tkinter.StringVar(app, "Video: 0/0")

completed_videos = tkinter.IntVar(value=0)   # To track completed video count
total_videos = tkinter.IntVar(value=0)       # To track total video count
# Variables to track progress
video_title = tkinter.StringVar(value="")
current_video_progress = tkinter.StringVar(value="...")
total_videos_count = tkinter.IntVar(value=0)
completed_videos_count = tkinter.IntVar(value=0)


# Functions
def start_download():
    completed_videos.set(0)  # Reset the completed video count
    total_videos.set(0)  # Reset the total video count

    """ Start the download in a separate thread to keep the UI responsive. """
    settings["download_path"] = download_path.get()
    save_settings()
    download_settings = {
        'url': link.get(),
        'video_format': video_format.get(),
        'video_quality': video_quality.get(),
        'audio_format': audio_format.get(),
        'audio_quality': audio_quality.get(),
        'audio_only': audio_only.get(),
        'auto_convert': auto_convert.get(),
        'playlist': download_playlist.get(),
        'download_directory': download_path.get()
    }
    threading.Thread(target=download_video, args=(download_settings,), daemon=True).start()


def convert_video(download_settings):
    """ Convert the downloaded video to the desired format if required. """
    original_file = os.path.join(download_settings['download_directory'], f"{download_settings['title']}.{download_settings['ext']}")
    target_file = os.path.join(download_settings['download_directory'], f"{download_settings['title']}.{download_settings['video_format']}")
    if original_file != target_file:
        CTkMessagebox(title="Info", message="Converting video to desired format...", icon="info")
        command = [
            "ffmpeg", "-i", original_file, "-c:v", "copy", "-c:a", "copy", target_file
        ]
        subprocess.run(command)
        CTkMessagebox(title="Info", message="Conversion complete!", icon="info")


# Function to update the progress label for the number of videos downloaded
def update_video_progress():
    completed_videos.set(completed_videos.get())
    playlist_progress_label.configure(text=f"Downloaded {int(completed_videos_count.get()/2) + 1} / {total_videos_count.get()} Video(s)")


# Download video function with yt-dlp hook
def download_video(download_settings):
    """ Download the video or playlist using yt-dlp with the specified settings. """

    def my_hook(d):
        if d['status'] == 'downloading':
            percent_str = re.sub(r'\x1b\[.*?m', '', d['_percent_str']).strip()  # Clean the percentage string

            # Extract additional data for more detailed progress
            total_size = d.get('total_bytes', 0) / (1024 * 1024) if d.get('total_bytes') else 0  # Total size in MB
            downloaded_size = d.get('downloaded_bytes', 0) / (1024 * 1024)  # Downloaded size in MB
            speed = d.get('speed', 0) / (1024 * 1024) if d.get('speed') else 0  # Download speed in MB/s
            eta = d.get('eta', 0)  # ETA in seconds

            # Safely format and display data, handle None values
            speed_str = f"{speed:.2f}MB/s" if speed else "N/A"
            eta_str = f"{eta:.0f}s" if eta else "N/A"
            total_size_str = f"{total_size:.2f}MB" if total_size else "N/A"

            try:
                # Update progress bar and labels
                progress_bar.set(float(percent_str.replace('%', '')) / 100)
                current_video_progress.set(f"{percent_str} Downloaded, {speed_str}, ETA: {eta_str}")
                title = d['info_dict'].get('title', 'Unknown Title')
                video_title.set(f"Title: {title}")
                title_label.update()

                # Old Progress bar for testing
                # progress_bar.set(float(percent_str.replace('%', '')) / 100)
                # progress_percentage.configure(text=f"Downloading... {percent_str} complete")
                # progress_percentage.update()
            except ValueError as e:
                print(f"Error converting progress to float: {str(e)}")

        elif d['status'] == 'finished':
            update_video_progress()
            if completed_videos.get() == total_videos.get():
                CTkMessagebox(title="Info", message="Playlist Download Successfully Completed!", icon="info")

        elif d['status'] == 'error':
            current_video_progress.set("Error occurred!")

            # progress_percentage.configure(text="Error occurred!", text_color='red')
            # progress_percentage.update()

    # Handle audio/video format
    format_str = f"bestaudio[ext={download_settings['audio_format']}]"
    if not download_settings['audio_only']:
        format_str = f"bestvideo[ext={download_settings['video_format']}]+bestaudio/best"

    # Check if it's a playlist and get the total number of videos
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
            info = ydl.extract_info(download_settings['url'], download=False)
            if 'entries' in info:  # It's a playlist
                total_videos_count.set(len(info['entries']))  # Set the total number of videos
            else:
                total_videos_count.set(1)  # Single video
        playlist_progress_label.configure(
            # Divide completed videos by 2 since yt-dlp counts video and audio streams separately
            text=f"Downloaded {int(completed_videos_count.get()/2) + 1} / {total_videos_count.get()} Video(s)")
    except Exception as e:
        print(f"Error fetching playlist info: {e}")
        total_videos.set(0)
        playlist_progress_label.configure(text="Invalid link")

    # yt-dlp options for downloading
    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(download_settings['download_directory'], '%(title)s.%(ext)s'),
        'noplaylist': not download_settings['playlist'],
        'merge_output_format': video_format.get(),
        'progress_hooks': [my_hook],
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': video_format.get()
        }] if not download_settings['audio_only'] else []
    }

    # Start download
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([download_settings['url']])
    except yt_dlp.utils.DownloadError as e:
        CTkMessagebox(title="Error", message=f"Download error: {str(e)}", icon="cancel")

# Automatically update preview when link is pasted
def on_link_change(*args):
    update_preview()

link = tkinter.StringVar()
link.trace_add('write', on_link_change)


# Function to update the video or playlist preview asynchronously

def is_valid_url(url):
    # Simple URL validation using regex
    url_regex = re.compile(
        r'^(https?:\/\/)?'  # http:// or https://
        r'((([a-z\d]([a-z\d-]*[a-z\d])*)\.)+[a-z]{2,}|'  # domain
        r'((\d{1,3}\.){3}\d{1,3}))'  # OR ip (v4) address
        r'(\:\d+)?(\/[-a-z\d%_.~+]*)*'  # port and path
        r'(\?[;&a-z\d%_.~+=-]*)?'  # query string
        r'(\#[-a-z\d_]*)?$', re.I)
    return re.match(url_regex, url) is not None

# Container to store image references and prevent garbage collection
image_container = []  # This ensures that the images are not garbage collected

def update_preview():
    """ Update the video or playlist preview section with thumbnail and details. """
    video_url = link.get()  # Assuming 'link' is a StringVar with the URL entered by the user

    # Ensure the URL is valid before continuing
    if not is_valid_url(video_url):
        handle_invalid_link()
        print("Error: Invalid URL")
        return

    ydl_opts = {'quiet': True, 'skip_download': True}

    # Display loading message while fetching media info
    thumbnail_label.configure(text="Getting Media Information...", image=None)
    title_label.configure(text="Fetching title...", font=("Courier New", 14, "bold"))
    author_label.configure(text="Fetching author...", font=("Courier New", 14, "bold"))
    duration_label.configure(text="Fetching duration...", font=("Courier New", 14, "bold"))
    playlist_progress_label.configure(text="")

    # Fetch media info in a separate thread to keep the UI responsive
    def fetch_media_info():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)

                # Playlist or single video?
                if 'entries' in info:  # It's a playlist
                    thumbnail_url = info['entries'][0]['thumbnail']
                    video_title.set(info.get('title', 'Playlist'))
                    video_author = info.get('uploader', 'Unknown uploader')
                    video_duration = sum([entry['duration'] for entry in info['entries']])
                    playlist_count = len(info['entries'])
                else:  # Single video
                    thumbnail_url = info.get('thumbnail')
                    video_title.set(info.get('title', ''))
                    video_author = info.get('uploader', 'Unknown uploader')
                    video_duration = info.get('duration', 0)
                    playlist_count = 1

                # Fetch the thumbnail image
                response = requests.get(thumbnail_url)
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img = img.resize((480, 270), Image.LANCZOS)

                global thumbnail_image

                # Use CTkImage and store it in the container to prevent garbage collection
                thumbnail_image = customtkinter.CTkImage(light_image=img, dark_image=img, size=(480, 270))
                image_container.append(thumbnail_image)  # Store in container to keep reference

                # Schedule the UI update from the main thread using app.after()
                app.after(0, lambda: update_preview_ui(thumbnail_image, video_title, video_author, video_duration,
                                                       playlist_count))

        except Exception as e:
            app.after(0, lambda: handle_invalid_link())
            print(f"Error fetching media info: {e}")

    # Start the fetching process in a new thread
    threading.Thread(target=fetch_media_info).start()

def update_preview_ui(thumbnail_image, video_title, video_author, video_duration, playlist_count):
    """ Update the UI with the fetched video or playlist information. """
    # Directly update the image without clearing
    thumbnail_label.configure(image=thumbnail_image, text="")
    title_label.configure(text=f"Title: {video_title.get()}", font=("Courier New", 14, "bold"))
    author_label.configure(text=f"Author: {video_author}", font=("Courier New", 14, "bold"))
    duration_label.configure(text=f"Duration: {video_duration // 60}m {video_duration % 60}s", font=("Courier New", 14, "bold"))
    playlist_progress_label.configure(text=f"Videos: {playlist_count}")

def handle_invalid_link():
    """ Handle invalid link cases. """
    thumbnail_label.configure(image=None, text="Invalid Link")
    title_label.configure(text="Title: Not available")
    author_label.configure(text="Author: Not available")
    duration_label.configure(text="Duration: Not available")



# Update the label displaying the download path
def choose_download_path():
    selected_directory = tkinter.filedialog.askdirectory()  # Open directory selection dialog
    if selected_directory:
        download_path.set(selected_directory)  # Update the StringVar with the selected directory
        download_path_label.configure(text=f"Download Path: {download_path.get()}")  # Update the label in the UI


def open_settings():
    """ Opens settings dialog for the user to adjust preferences. """
    settings_window = customtkinter.CTkToplevel(app)
    settings_window.title("Settings")
    settings_window.geometry("400x400")
    settings_window.transient(app)

    # Theme (light/dark mode) option
    theme_label = customtkinter.CTkLabel(settings_window, text="Theme:", font=custom_font)
    theme_label.grid(row=0, column=0, pady=10, padx=10, sticky="w")

    theme_option = customtkinter.CTkOptionMenu(settings_window, values=["dark", "light", "system"],
                                               variable=tkinter.StringVar(value=settings.get("theme", "dark")),
                                               command=lambda value: save_theme(value))
    theme_option.grid(row=0, column=1, pady=10, padx=10, sticky="e")

    # Built-in color theme option (blue, dark-blue, green)
    color_label = customtkinter.CTkLabel(settings_window, text="Color Theme:", font=custom_font)
    color_label.grid(row=1, column=0, pady=10, padx=10, sticky="w")

    # Options limited to valid built-in themes
    color_option = customtkinter.CTkOptionMenu(settings_window, values=["blue", "green", "dark-blue"],
                                               variable=tkinter.StringVar(value=settings.get("color", "blue")),
                                               command=lambda value: save_color(value))
    color_option.grid(row=1, column=1, pady=10, padx=10, sticky="e")

    # Save theme to settings
    def save_theme(value):
        settings["theme"] = value
        save_settings()
        customtkinter.set_appearance_mode(value)

    # Save color theme to settings
    def save_color(value):
        settings["color"] = value
        save_settings()
        customtkinter.set_default_color_theme(value)


# Rearranging the button positions
settings_button = customtkinter.CTkButton(bottom_frame, text="Settings", command=open_settings,
                                          corner_radius=corner_radius)
download_button = customtkinter.CTkButton(bottom_frame, text="Download", command=start_download,
                                          corner_radius=corner_radius)
open_folder_button = customtkinter.CTkButton(bottom_frame, text="Open Folder", command=lambda: os.startfile(
    download_path.get()) if platform.system() == "Windows" else subprocess.Popen(["open", download_path.get()]),
                                             corner_radius=corner_radius)

playlist_toggle = customtkinter.CTkSwitch(bottom_frame, text="Download Playlist", variable=download_playlist, onvalue=True,
                                        offvalue=False, font=custom_font, corner_radius=corner_radius)

# Adding the Automatic Conversion Checkbox under Download Audio Only
auto_convert_checkbox = customtkinter.CTkCheckBox(bottom_frame, text="Automatic Conversion", variable=auto_convert,
                                                  onvalue=True, offvalue=False, font=custom_font)

download_as_audio = customtkinter.CTkCheckBox(bottom_frame, text="Download Audio Only", variable=audio_only,
                                              onvalue=True, offvalue=False, font=custom_font)
quality_label = customtkinter.CTkLabel(bottom_frame, text="Video/Audio Quality", font=custom_font,
                                       corner_radius=corner_radius)
format_label = customtkinter.CTkLabel(bottom_frame, text="Video/Audio Format", font=custom_font,
                                      corner_radius=corner_radius)

video_quality_combobox = customtkinter.CTkOptionMenu(master=bottom_frame,
                                                     values=["best", "2160p", "1440p", "1080p", "720p", "480p", "360p"],
                                                     variable=video_quality, corner_radius=corner_radius)
video_format_combobox = customtkinter.CTkOptionMenu(master=bottom_frame, values=["mp4", "mkv", "flv", "webm"],
                                                    variable=video_format, corner_radius=corner_radius)

audio_quality_combobox = customtkinter.CTkOptionMenu(master=bottom_frame,
                                                     values=["best", "320Kbps", "256Kbps", "192Kbps", "128Kbps"],
                                                     variable=audio_quality, corner_radius=corner_radius)
audio_format_combobox = customtkinter.CTkOptionMenu(master=bottom_frame, values=["mp3", "m4a", "aac", "opus", "vorbis"],
                                                    variable=audio_format, corner_radius=corner_radius)

# Place bottom frame widgets in grid
settings_button.grid(row=3, column=0, padx=5, pady=15)
download_button.grid(row=3, column=1, padx=5, pady=15)
open_folder_button.grid(row=3, column=2, padx=5, pady=15)
playlist_toggle.grid(row=0, column=0, padx=5, pady=5)
download_as_audio.grid(row=1, column=0, padx=5, pady=5)
quality_label.grid(row=0, column=1, padx=5, pady=5)
video_quality_combobox.grid(row=1, column=1, padx=5, pady=5)
audio_quality_combobox.grid(row=2, column=1, padx=5, pady=5)
format_label.grid(row=0, column=2, padx=5, pady=5)
video_format_combobox.grid(row=1, column=2, padx=5, pady=5)
audio_format_combobox.grid(row=2, column=2, padx=5, pady=5)

# Placing the checkbox directly below the "Download Audio Only" checkbox
auto_convert_checkbox.grid(row=2, column=0, padx=5, pady=5)


# Labels for the preview section
thumbnail_label = customtkinter.CTkLabel(top_right_frame, text="Thumbnail", corner_radius=corner_radius,
                                         text_color="light blue")
thumbnail_label.grid(row=0, column=0, pady=5)
title_label = customtkinter.CTkLabel(top_right_frame, text="Title: ", font=custom_font, corner_radius=corner_radius,
                                     text_color="light blue")
title_label.grid(row=2, column=0, pady=5)
author_label = customtkinter.CTkLabel(top_right_frame, text="Author: ", font=custom_font, corner_radius=corner_radius,
                                      text_color="light blue")
author_label.grid(row=3, column=0, pady=5)
duration_label = customtkinter.CTkLabel(top_right_frame, text="Duration: ", font=custom_font,
                                        corner_radius=corner_radius, text_color="light blue")
duration_label.grid(row=4, column=0, pady=5)
playlist_progress_label = customtkinter.CTkLabel(top_right_frame, text=playlist_progress.get(),
                                                 font=(custom_font, 13, "bold"), text_color="gold",
                                                 corner_radius=corner_radius)
playlist_progress_label.grid(row=5, column=0, pady=5)

# Top left frame widgets
logo = customtkinter.CTkImage(dark_image=Image.open(resource_path("media_downloader_picture.png")),
                              light_image=Image.open(resource_path("media_downloader_picture.png")), size=(175, 175))
logo_label = customtkinter.CTkLabel(top_left_frame, text="", image=logo, font=custom_font, corner_radius=corner_radius)
title = customtkinter.CTkLabel(top_left_frame, text="Enter Media Link:", font=custom_font,
                               corner_radius=corner_radius)
link_entry = customtkinter.CTkEntry(top_left_frame, width=360, height=35, textvariable=link, font=custom_font,
                                    corner_radius=corner_radius)
progress_bar = customtkinter.CTkProgressBar(top_left_frame, width=360, corner_radius=corner_radius)

#progress_percentage = customtkinter.CTkLabel(top_left_frame, text="0%", font=custom_font, text_color="green",
#                                             corner_radius=corner_radius)
download_path_label = customtkinter.CTkLabel(top_left_frame, text=f"Download Path: {download_path.get()}",
                                             text_color="gold", font=custom_font, corner_radius=corner_radius)
file_path = customtkinter.CTkButton(top_left_frame, text="Choose Download Path",
                                    command=choose_download_path,
                                    corner_radius=corner_radius)

current_video_progress_label = customtkinter.CTkLabel(
    top_left_frame, textvariable=current_video_progress, font=("Courier New", 13, "bold"), text_color="light blue")

# Place top left frame widgets in grid
logo_label.grid(row=0, column=0, pady=5)
title.grid(row=1, column=0, pady=5)
link_entry.grid(row=2, column=0, pady=5)
progress_bar.grid(row=3, column=0, pady=5)
progress_bar.set(0)
# progress_percentage.grid(row=4, column=0, pady=5)
current_video_progress_label.grid(row=4, column=0, pady=5)  # Replaces progress_percentage with newer progress_label
download_path_label.grid(row=5, column=0, pady=5)
file_path.grid(row=6, column=0, pady=10)

app.mainloop()