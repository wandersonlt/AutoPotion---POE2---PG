import customtkinter as ctk
import tkinter.messagebox as messagebox
import requests
from datetime import datetime
import threading
import time

class Dashboard:
    def __init__(self, api_url, license_key, machine_id, version):
        self.api_url = api_url
        self.license_key = license_key
        self.machine_id = machine_id
        self.version = version
        self.license_info = None
        
        self.window = ctk.CTk()
        self.window.title("License Manager - Dashboard")
        self.window.geometry("900x600")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"900x600+{x}+{y}")
        
        self.setup_ui()
        self.load_license_info()
        
        self.refresh_running = True
        self.refresh_thread = threading.Thread(target=self.auto_refresh, daemon=True)
        self.refresh_thread.start()
    
    def setup_ui(self):
        self.main_container = ctk.CTkFrame(self.window)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        top_bar = ctk.CTkFrame(self.main_container, height=60, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            top_bar,
            text="License Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        refresh_button = ctk.CTkButton(
            top_bar,
            text="Refresh",
            width=100,
            command=self.load_license_info
        )
        refresh_button.pack(side="right", padx=5)
        
        info_frame = ctk.CTkFrame(self.main_container)
        info_frame.pack(fill="x", pady=10)
        
        self.info_labels = {}
        info_items = [
            ("License Key", "key"),
            ("Plan", "plan"),
            ("Status", "status"),
            ("Expires At", "expires_at"),
            ("Remaining Days", "remaining_days"),
        ]
        
        for i, (label, key) in enumerate(info_items):
            row = i // 2
            col = i % 2
            
            label_widget = ctk.CTkLabel(
                info_frame,
                text=f"{label}:",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            label_widget.grid(row=row, column=col*2, sticky="w", padx=20, pady=10)
            
            value_widget = ctk.CTkLabel(
                info_frame,
                text="Loading...",
                font=ctk.CTkFont(size=14)
            )
            value_widget.grid(row=row, column=col*2+1, sticky="w", padx=20, pady=10)
            
            self.info_labels[key] = value_widget
        
        self.status_bar = ctk.CTkLabel(
            self.main_container,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_bar.pack(side="bottom", fill="x", pady=(20, 0))
    
    def load_license_info(self):
        def fetch():
            try:
                response = requests.post(
                    f"{self.api_url}/api/verify-license",
                    params={"license_key": self.license_key, "machine_id": self.machine_id},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.license_info = data.get("license", {})
                    self.window.after(0, self.update_ui)
                else:
                    self.window.after(0, lambda: self.status_bar.configure(
                        text="Failed to load license info", text_color="red"
                    ))
            except Exception as e:
                self.window.after(0, lambda: self.status_bar.configure(
                    text=f"Error: {str(e)}", text_color="red"
                ))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def update_ui(self):
        if not self.license_info:
            return
        
        self.info_labels["key"].configure(text=self.license_info.get("key", "N/A"))
        self.info_labels["plan"].configure(text=self.license_info.get("plan", "N/A"))
        
        status = self.license_info.get("status", "N/A")
        status_color = "green" if status == "ACTIVE" else "red"
        self.info_labels["status"].configure(text=status, text_color=status_color)
        
        expires_at = self.license_info.get("expires_at", "N/A")
        if expires_at != "N/A":
            try:
                expires_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                expires_at = expires_date.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        self.info_labels["expires_at"].configure(text=expires_at)
        
        remaining_days = self.license_info.get("remaining_days")
        if remaining_days is not None:
            self.info_labels["remaining_days"].configure(text=f"{remaining_days} days")
        else:
            self.info_labels["remaining_days"].configure(text="Lifetime")
        
        self.status_bar.configure(text="Last updated: " + datetime.now().strftime("%H:%M:%S"), text_color="gray")
    
    def auto_refresh(self):
        while self.refresh_running:
            time.sleep(60)
            if self.refresh_running:
                self.load_license_info()
    
    def run(self):
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
    
    def on_closing(self):
        self.refresh_running = False
        self.window.destroy()
