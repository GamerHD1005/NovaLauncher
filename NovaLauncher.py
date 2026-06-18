import customtkinter as ctk
import minecraft_launcher_lib as mll
import subprocess
import threading
import uuid
import json
import os
import requests
from PIL import Image
import io
import time
import sys

minecraft_directory = "./.minecraft_data"
config_file = "client_config.json"

class NovaLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue") 

        self.config = self.load_config()
        self.current_theme = self.config.get("theme", "cyan")
        self.theme_color = self.get_color_by_theme(self.current_theme)

        self.title("NOVALAUNCHER")
        self.geometry("920x600")
        self.resizable(False, False)
        self.configure(fg_color="#090909")

        self.account_type = self.config.get("account_type", "Offline")
        if self.account_type == "Premium":
            self.current_player = self.config.get("premium_username", "PremiumUser")
        else:
            self.current_player = self.config.get("last_user", "NovaLauncher")
            
        self.selected_version = self.config.get("version", "1.21.1")
        self.selected_loader = self.config.get("loader", "Vanilla") 

        self.sidebar = ctk.CTkFrame(self, width=65, fg_color="#111111", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content_frame.pack(side="left", fill="both", expand=True)

        self.start_time = 0
        self.last_bytes = 0
        self.is_downloading = False
        self.fake_progress = 0
        
        self.status_text1 = "LAUNCH"
        self.status_text2 = ""
        self.status_color2 = self.theme_color

        self.build_sidebar()
        self.show_play_section()
        self.update_ui_loop()

    def load_config(self):
        if os.path.exists(config_file):
            with open(config_file, "r") as f: return json.load(f)
        return {"accounts": {}, "theme": "cyan", "version": "1.21.1", "account_type": "Offline", "loader": "Vanilla"}

    def save_config(self):
        with open(config_file, "w") as f: json.dump(self.config, f)

    def get_color_by_theme(self, name):
        themes = {"cyan": "#00ffcc", "purple": "#a020f0", "red": "#ff3333", "gold": "#ffcc00"}
        return themes.get(name, "#00ffcc")

    def build_sidebar(self):
        logo = ctk.CTkLabel(self.sidebar, text="⚡", font=ctk.CTkFont(size=24), text_color=self.theme_color)
        logo.pack(pady=(20, 30))

        self.btn_play = ctk.CTkButton(self.sidebar, text="▶", width=45, height=45, fg_color="#1a1a1a", hover_color="#252525", text_color="#ffffff", font=ctk.CTkFont(size=16), command=self.show_play_section)
        self.btn_play.pack(pady=10)

        self.btn_acc = ctk.CTkButton(self.sidebar, text="👤", width=45, height=45, fg_color="transparent", hover_color="#1a1a1a", text_color="#888888", font=ctk.CTkFont(size=16), command=self.show_account_section)
        self.btn_acc.pack(pady=10)

        self.btn_settings = ctk.CTkButton(self.sidebar, text="⚙", width=45, height=45, fg_color="transparent", hover_color="#1a1a1a", text_color="#888888", font=ctk.CTkFont(size=16), command=self.show_settings_section)
        self.btn_settings.pack(pady=10)

    def reset_sidebar_colors(self, active_btn):
        for btn in [self.btn_play, self.btn_acc, self.btn_settings]:
            btn.configure(fg_color="transparent", text_color="#888888")
        active_btn.configure(fg_color="#1a1a1a", text_color=self.theme_color)

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_play_section(self):
        self.clear_content()
        self.reset_sidebar_colors(self.btn_play)

        center_area = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        center_area.pack(side="left", fill="both", expand=True)

        # HIER WIRD DER NAME DYNAMISCH AUSGELASTET
        title = ctk.CTkLabel(center_area, text=self.current_player.upper(), font=ctk.CTkFont(family="Helvetica", size=32, weight="bold"), text_color="#ffffff")
        title.place(relx=0.5, y=70, anchor="center")

        skin_label = ctk.CTkLabel(center_area, text="Lade Charakter...")
        skin_label.place(relx=0.5, rely=0.45, anchor="center")

        def fetch_skin():
            try:
                url = f"https://mc-heads.net/body/{self.current_player}/240"
                res = requests.get(url, timeout=4)
                if res.status_code == 200:
                    img = Image.open(io.BytesIO(res.content))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(140, 260))
                    if skin_label.winfo_exists():
                        skin_label.configure(image=ctk_img, text="")
            except: 
                if skin_label.winfo_exists():
                    skin_label.configure(text="[Offline-Skin]")
        threading.Thread(target=fetch_skin, daemon=True).start()

        news_area = ctk.CTkFrame(self.content_frame, width=240, fg_color="#0e0e0e", corner_radius=0)
        news_area.pack(side="right", fill="y")
        news_area.pack_propagate(False)

        ntitle = ctk.CTkLabel(news_area, text="% s | Mbps Anzeige", font=ctk.CTkFont(size=12, weight="bold"), text_color="#555555")
        ntitle.pack(anchor="w", padx=20, pady=(25, 5))

        box = ctk.CTkFrame(news_area, fg_color="#131313")
        box.pack(fill="both", expand=True, padx=15, pady=10)
        
        display_loader = "" if self.selected_loader == "Vanilla" else f" ({self.selected_loader})"
        c_text = ctk.CTkLabel(box, text=f"v4.2.0-NovaLauncher\n\n- Java Fallback & Fix\n- Erkennt Ordner-Versionen\n- Download-Fortschritt stabil\n\nAuswahl: {self.selected_version}{display_loader}", font=ctk.CTkFont(size=11), text_color="#777777", justify="left")
        c_text.pack(anchor="w", padx=15, pady=15)

        btn_frame = ctk.CTkFrame(center_area, fg_color="#121212", height=60, width=290, border_width=1, border_color="#222222")
        btn_frame.place(relx=0.5, rely=0.85, anchor="center")
        btn_frame.pack_propagate(False)

        self.text_container = ctk.CTkFrame(btn_frame, fg_color="transparent", cursor="hand2")
        self.text_container.pack(side="left", fill="both", expand=True)

        self.lbl_launch = ctk.CTkLabel(self.text_container, text=self.status_text1, font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffffff")
        self.lbl_launch.place(relx=0.5, rely=0.30, anchor="center")

        loader_text = f" - {self.selected_loader}" if self.selected_loader != "Vanilla" else ""
        if not self.is_downloading:
            self.status_text2 = f"{self.selected_version}{loader_text}"
            self.status_color2 = self.theme_color
            
        self.lbl_sub = ctk.CTkLabel(self.text_container, text=self.status_text2, font=ctk.CTkFont(size=11, weight="bold"), text_color=self.status_color2)
        self.lbl_sub.place(relx=0.5, rely=0.70, anchor="center")

        self.text_container.bind("<Button-1>", lambda e: self.start_game())
        self.lbl_launch.bind("<Button-1>", lambda e: self.start_game())
        self.lbl_sub.bind("<Button-1>", lambda e: self.start_game())

        drop_btn = ctk.CTkButton(btn_frame, text="▼", width=50, height=60, fg_color="#181818", hover_color="#222222", corner_radius=0, command=self.show_version_selector)
        drop_btn.pack(side="right")

    def show_account_section(self):
        self.clear_content()
        self.reset_sidebar_colors(self.btn_acc)

        title = ctk.CTkLabel(self.content_frame, text="ACCOUNT MANAGER", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=30)

        box = ctk.CTkFrame(self.content_frame, fg_color="#111111", width=430, height=360)
        box.pack(pady=10)
        box.pack_propagate(False)

        ctk.CTkLabel(box, text="Aktueller Status: " + self.account_type, font=ctk.CTkFont(weight="bold"), text_color=self.theme_color).pack(pady=15)

        ctk.CTkLabel(box, text="Offline-Konto Username:").pack()
        name_entry = ctk.CTkEntry(box, width=250, fg_color="#161616", border_color="#252525")
        name_entry.pack(pady=5)
        if self.account_type == "Offline": name_entry.insert(0, self.current_player)

        def set_offline():
            name = name_entry.get().strip()
            if name:
                self.current_player = name
                self.account_type = "Offline"
                self.config["last_user"] = name
                self.config["account_type"] = "Offline"
                self.save_config()
                self.show_play_section()

        ctk.CTkButton(box, text="Als Offline-Konto nutzen", fg_color="#222222", hover_color="#333333", command=set_offline).pack(pady=10)

    def show_settings_section(self):
        self.clear_content()
        self.reset_sidebar_colors(self.btn_settings)

        title = ctk.CTkLabel(self.content_frame, text="CLIENT SETTINGS", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(pady=30)

        box = ctk.CTkFrame(self.content_frame, fg_color="#111111", width=400, height=250)
        box.pack(pady=10)
        box.pack_propagate(False)

        ctk.CTkLabel(box, text="CLIENT DESIGN FARBE ÄNDERN", font=ctk.CTkFont(size=12, weight="bold"), text_color="#777777").pack(pady=20)

        colors = ["cyan", "purple", "red", "gold"]
        def change_color(chosen_color):
            self.current_theme = chosen_color
            self.theme_color = self.get_color_by_theme(chosen_color)
            self.config["theme"] = chosen_color
            self.save_config()
            self.build_sidebar()
            self.show_settings_section()

        color_menu = ctk.CTkOptionMenu(box, values=colors, fg_color="#161616", button_color="#222222", command=change_color)
        color_menu.pack(pady=5)
        color_menu.set(self.current_theme)

    def show_version_selector(self):
        pop = ctk.CTkToplevel(self)
        pop.title("Versionen")
        pop.geometry("400x480")
        pop.resizable(False, False)
        pop.configure(fg_color="#0d0d0d")
        pop.attributes("-topmost", True)

        ctk.CTkLabel(pop, text="MINECRAFT VERSION WÄHLEN", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.theme_color).pack(pady=15)

        scroll = ctk.CTkScrollableFrame(pop, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=10)

        version_data = [
            ("1.21.1", "🌟 Neueste Version"),
            ("1.20.4", "🛠️ Perfekt für Mods"),
            ("1.19.4", "🌲 Wild Update Stable"),
            ("1.18.2", "🏔️ Caves & Cliffs"),
            ("1.16.5", "🔥 Nether Update Klassiker"),
            ("1.12.2", "🔌 Riesen Modpack-Klassiker"),
            ("1.8.9", "⚔️ Bestes PvP / Bedwars")
        ]

        for ver, desc in version_data:
            f = ctk.CTkFrame(scroll, fg_color="#141414", height=50, border_width=1, border_color="#222222")
            f.pack(fill="x", pady=4)
            f.pack_propagate(False)

            lbl = ctk.CTkLabel(f, text=f"  {ver}  -  {desc}", font=ctk.CTkFont(size=11, weight="bold"))
            lbl.pack(side="left", padx=10)

            def open_engine_menu(v=ver):
                pop.destroy()
                self.show_mod_loader_menu(v)

            b = ctk.CTkButton(f, text="Wählen", width=70, height=30, fg_color="#1f538d", command=open_engine_menu)
            b.pack(side="right", padx=10, pady=10)

    def show_mod_loader_menu(self, version):
        sub_pop = ctk.CTkToplevel(self)
        sub_pop.title("Engine Setup")
        sub_pop.geometry("360x320")
        sub_pop.resizable(False, False)
        sub_pop.configure(fg_color="#0d0d0d")
        sub_pop.attributes("-topmost", True)

        ctk.CTkLabel(sub_pop, text=f"MOD ENGINE FÜR {version}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffffff").pack(pady=15)

        def select_engine(loader):
            self.selected_version = version
            self.selected_loader = loader
            self.config["version"] = version
            self.config["loader"] = loader
            self.save_config()
            self.show_play_section()
            sub_pop.destroy()

        fabric_available = mll.fabric.is_minecraft_version_supported(version)
        
        forge_available = False
        try:
            forge_list = mll.forge.get_forge_version_list(version)
            if forge_list: forge_available = True
        except: pass

        ctk.CTkButton(sub_pop, text="Vanilla (Standard Minecraft)", fg_color="#1c1c1c", hover_color="#252525", width=260, height=40, command=lambda: select_engine("Vanilla")).pack(pady=8)
        
        fab_btn = ctk.CTkButton(sub_pop, text="Fabric Engine 🧬" if fabric_available else "Fabric (Nicht verfügbar)", fg_color="#2ea44f" if fabric_available else "#333333", state="normal" if fabric_available else "disabled", width=260, height=40, command=lambda: select_engine("Fabric"))
        fab_btn.pack(pady=8)
        
        for_btn = ctk.CTkButton(sub_pop, text="Forge Engine ⚙️" if forge_available else "Forge (Nicht verfügbar)", fg_color="#df6c1e" if forge_available else "#333333", state="normal" if forge_available else "disabled", width=260, height=40, command=lambda: select_engine("Forge"))
        for_btn.pack(pady=8)

    def update_ui_loop(self):
        try:
            if hasattr(self, 'lbl_launch') and self.lbl_launch.winfo_exists():
                self.lbl_launch.configure(text=self.status_text1)
            if hasattr(self, 'lbl_sub') and self.lbl_sub.winfo_exists():
                self.lbl_sub.configure(text=self.status_text2, text_color=self.status_color2)
        except:
            pass
        self.after(100, self.update_ui_loop)

    def simulate_progress_loop(self):
        import random
        mbps = random.uniform(13.2, 17.1) 

        while self.is_downloading:
            time.sleep(0.4)
            if not self.is_downloading: break
            
            self.fake_progress += random.uniform(0.8, 2.1)
            if self.fake_progress > 99: self.fake_progress = 99.6
            
            percent = int(self.fake_progress)
            mbps = max(5.0, mbps + random.uniform(-1.0, 1.0))
            
            rem_seconds = int((100 - percent) * (3.5 / max(1, mbps)))
            if rem_seconds < 60:
                time_text = f"{rem_seconds}s"
            else:
                time_text = f"{rem_seconds // 60}m {rem_seconds % 60}s"

            self.status_text1 = f"DOWNLOADING {percent}%"
            self.status_text2 = f"{mbps:.1f} Mbps | Noch {time_text}"
            self.status_color2 = "#aaaaaa"

    def start_game(self):
        self.text_container.unbind("<Button-1>")
        self.lbl_launch.unbind("<Button-1>")
        self.lbl_sub.unbind("<Button-1>")
        
        self.status_text1 = "STARTING..."
        self.status_text2 = "Scanne Spieldateien..."
        self.status_color2 = "gray"
        
        threading.Thread(target=self.launch_engine, daemon=True).start()

    def launch_engine(self):
        try:
            if not os.path.exists(minecraft_directory):
                os.makedirs(minecraft_directory)

            active_launch_version = self.selected_version
            needs_download = True

            if os.path.exists(os.path.join(minecraft_directory, "versions")):
                installed_folders = os.listdir(os.path.join(minecraft_directory, "versions"))
                
                if self.selected_loader == "Fabric":
                    for folder in installed_folders:
                        if "fabric" in folder.lower() and self.selected_version in folder:
                            active_launch_version = folder
                            needs_download = False
                            break
                elif self.selected_loader == "Forge":
                    for folder in installed_folders:
                        if "forge" in folder.lower() and self.selected_version in folder:
                            active_launch_version = folder
                            needs_download = False
                            break
                elif self.selected_loader == "Vanilla":
                    if self.selected_version in installed_folders:
                        needs_download = False

            if needs_download:
                self.is_downloading = True
                self.fake_progress = 0
                threading.Thread(target=self.simulate_progress_loop, daemon=True).start()

                mll.install.install_minecraft_version(self.selected_version, minecraft_directory)
                
                if self.selected_loader == "Fabric":
                    mll.fabric.install_fabric(self.selected_version, minecraft_directory)
                elif self.selected_loader == "Forge":
                    forge_ver = mll.forge.get_forge_version_list(self.selected_version)
                    if forge_ver:
                        mll.forge.install_forge_version(forge_ver[0], minecraft_directory)

                if os.path.exists(os.path.join(minecraft_directory, "versions")):
                    installed_folders = os.listdir(os.path.join(minecraft_directory, "versions"))
                    for folder in installed_folders:
                        if self.selected_loader.lower() in folder.lower() and self.selected_version in folder:
                            active_launch_version = folder
                            break

            self.is_downloading = False
            self.status_text1 = "LAUNCHING..."
            self.status_text2 = "Initiiere Spieldaten..."
            self.status_color2 = self.theme_color
            time.sleep(1.0)

            java_path = mll.runtime.get_executable_path(self.selected_version, minecraft_directory)
            if not java_path:
                try:
                    mll.runtime.install_runtime(self.selected_version, minecraft_directory)
                    java_path = mll.runtime.get_executable_path(self.selected_version, minecraft_directory)
                except:
                    pass
            
            if not java_path:
                java_path = "javaw"

            options = {
                "username": self.current_player,
                "uuid": str(uuid.uuid4()),
                "token": "0",
                "jvmArguments": ["-Xmx2G", "-XX:+UnlockExperimentalVMOptions", "-XX:+UseG1GC"]
            }

            if self.account_type == "Premium" and "microsoft_auth_token" in self.config:
                options.update(self.config["microsoft_auth_token"])

            options["executablePath"] = java_path
            
            cmd = mll.command.get_minecraft_command(active_launch_version, minecraft_directory, options)
            
            self.withdraw()
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
            time.sleep(2.0)
            self.destroy()
            
        except Exception as e:
            self.is_downloading = False
            self.status_text1 = "START ERROR"
            self.status_text2 = "Fehler beim Booten"
            self.status_color2 = "red"

if __name__ == "__main__":
    app = NovaLauncher()
    app.mainloop()
