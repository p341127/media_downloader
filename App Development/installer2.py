import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys

class InstallerGUI:
    def __init__(self, root):
        self.root = root
        root.title("Multimedia Installer for yt-dlp and ffmpeg")
        root.geometry("500x320")
        root.resizable(False, False)

        # Styling
        style = ttk.Style()
        style.theme_use('clam')

        # Labels
        ttk.Label(root, text="Install or Manage yt-dlp and ffmpeg", font=('Helvetica', 16)).pack(pady=20)

        # Buttons
        ttk.Button(root, text="Check Installation", command=self.check_installation).pack(pady=5)
        ttk.Button(root, text="Install / Upgrade", command=self.install).pack(pady=5)
        ttk.Button(root, text="Remove", command=self.remove).pack(pady=5)
        ttk.Button(root, text="Install Missing Tools", command=self.install_missing_tools).pack(pady=5)

    def run_command(self, command, shell=False):
        try:
            subprocess.check_call(command, shell=shell)
            return True
        except subprocess.CalledProcessError:
            return False

    def check_installation(self):
        tools_installed = True
        if sys.platform.startswith('win32'):
            if not self.run_command("choco -v", shell=True):
                messagebox.showinfo("Missing Tool", "Chocolatey is not installed. Please install it.")
                tools_installed = False

        if sys.platform.startswith('darwin'):
            if not self.run_command("brew -v", shell=True):
                messagebox.showinfo("Missing Tool", "Homebrew is not installed. Please install it.")
                tools_installed = False

        if not tools_installed:
            return

        yt_dlp_installed = self.run_command("yt-dlp --version", shell=True)
        ffmpeg_installed = self.run_command("ffmpeg -version", shell=True)
        message = f"yt-dlp is {'installed' if yt_dlp_installed else 'not installed'}.\nffmpeg is {'installed' if ffmpeg_installed else 'not installed'}."
        messagebox.showinfo("Check Installation", message)

    def install_missing_tools(self):
        if sys.platform.startswith('win32'):
            self.run_command("Set-ExecutionPolicy Bypass -Scope Process -Force; iwr https://chocolatey.org/install.ps1 -UseBasicParsing | iex", shell=True)
        elif sys.platform.startswith('darwin'):
            self.run_command("/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"", shell=True)
        messagebox.showinfo("Installation", "Required tools have been installed. Please verify.")

    def install_yt_dlp(self):
        """Installs or upgrades yt-dlp using pip."""
        return self.run_command([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])

    def install_ffmpeg(self):
        """Installs or upgrades ffmpeg."""
        if sys.platform.startswith('linux'):
            return self.run_command("sudo apt-get install -y ffmpeg", shell=True)
        elif sys.platform.startswith('darwin'):
            return self.run_command("brew install ffmpeg", shell=True)
        elif sys.platform.startswith('win32'):
            return self.run_command("choco install ffmpeg", shell=True)

    def install(self):
        yt_dlp_status = self.install_yt_dlp()
        ffmpeg_status = self.install_ffmpeg()
        message = f"yt-dlp installation {'succeeded' if yt_dlp_status else 'failed'}.\nffmpeg installation {'succeeded' if ffmpeg_status else 'failed'}."
        messagebox.showinfo("Installation Results", message)

    def remove(self):
        yt_dlp_remove = self.run_command([sys.executable, "-m", "pip", "uninstall", "yt-dlp", "-y"])
        ffmpeg_remove = False
        if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            ffmpeg_remove = self.run_command("sudo apt-get remove -y ffmpeg", shell=True)
        elif sys.platform.startswith('win32'):
            ffmpeg_remove = self.run_command("choco uninstall ffmpeg", shell=True)
        message = f"yt-dlp removal {'succeeded' if yt_dlp_remove else 'failed'}.\nffmpeg removal {'succeeded' if ffmpeg_remove else 'failed'}."
        messagebox.showinfo("Removal Results", message)

def main():
    root = tk.Tk()
    gui = InstallerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
