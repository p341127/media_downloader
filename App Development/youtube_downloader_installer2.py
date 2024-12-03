import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import shutil
import os

class InstallerGUI:
    def __init__(self, root):
        self.root = root
        root.title("Multimedia Tool Installer")
        root.geometry("500x300")
        
        ttk.Label(root, text="Install or Uninstall YouTube Downloader", font=('Helvetica', 16)).pack(pady=20)
        ttk.Button(root, text="Install YouTube Downloader", command=self.install_downloader).pack(pady=10)
        ttk.Button(root, text="Uninstall YouTube Downloader", command=self.uninstall_downloader).pack(pady=10)

    def install_downloader(self):
        executable_path = os.path.join('dist', 'youtube_downloader')  # No .exe for Unix systems
        target_path = os.path.join(os.environ.get('HOME'), 'bin')
        os.makedirs(target_path, exist_ok=True)
        shutil.copy(executable_path, target_path)

        if sys.platform.startswith('win32'):
            self.add_to_path_windows(target_path)
        else:
            self.add_to_path_unix(target_path)

        messagebox.showinfo("Installation", "YouTube Downloader installed successfully.")

    def add_to_path_windows(self, path):
        subprocess.run(f'setx PATH "%PATH%;{path}"', shell=True)

    def add_to_path_unix(self, path):
        shell_config = '.bashrc'
        if os.path.exists(os.path.join(os.environ.get('HOME'), '.zshrc')):
            shell_config = '.zshrc'

        with open(os.path.join(os.environ.get('HOME'), shell_config), 'a') as file:
            file.write(f'\nexport PATH="$PATH:{path}"\n')

    def uninstall_downloader(self):
        target_path = os.path.join(os.environ.get('HOME'), 'bin', 'youtube_downloader')  # No .exe for Unix systems
        if os.path.exists(target_path):
            os.remove(target_path)
            messagebox.showinfo("Uninstallation", "YouTube Downloader uninstalled successfully.")
        else:
            messagebox.showinfo("Uninstallation", "YouTube Downloader not found.")

def main():
    root = tk.Tk()
    app = InstallerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
