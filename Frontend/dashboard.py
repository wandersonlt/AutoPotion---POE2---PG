import customtkinter as ctk
import tkinter.messagebox as messagebox
import requests
from datetime import datetime
import threading
import time
from settings import SettingsWindow

class Dashboard:
    def __init__(self, api_url, license_key, machine_id, version):
        self.api_url = api_url
        self.license_key = license_key
        self.machine_id = machine_id
        self.version = version
        self.license_info = None
        
        # Create window
        self.window = ctk.CTk()
        self.window.title("License Manager - Dashboard")
        self.window.geometry("900x600")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"900x600+{x}+{y}")
        
        self.setup_ui()
        self.load_license_info()
        
        # Start auto-refresh thread
        self.refresh_running = True
        self.refresh_thread = threading.Thread(target=self.auto_refresh, daemon=True)
        self.refresh_thread.start()
    
    def setup_ui(self):
        # Main container
        self.main_container = ctk.CTkFrame(self.window)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Top bar
        top_bar = ctk.CTkFrame(self.main_container, height=60, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            top_bar,
            text="License Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left")
        
        # Settings button
        settings_button = ctk.CTkButton(
            top_bar,
            text="⚙️ Settings",
            width=100,
            command=self.open_settings
        )
        settings_button.pack(side="right", padx=5)
        
        refresh_button = ctk.CTkButton(
            top_bar,
            text="🔄 Refresh",
            width=100,
            command=self.load_license_info
        )
        refresh_button.pack(side="right", padx=5)
        
        # License info frame
        info_frame = ctk.CTkFrame(self.main_container)
        info_frame.pack(fill="x", pady=10)
        
        # Grid for license info
        self.info_labels = {}
        info_items = [
            ("License Key", "license_key"),
            ("Plan", "plan"),
            ("Status", "status"),
            ("Expires At", "expires_at"),
            ("Remaining Days", "remaining_days"),
            ("Machine ID", "machine_id")
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
        
        # Progress bar for remaining days
        progress_frame = ctk.CTkFrame(self.main_container)
        progress_frame.pack(fill="x", pady=20)
        
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="License Validity:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.progress_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=20)
        self.progress_bar.pack(fill="x", padx=20, pady=5)
        
        # Actions frame
        actions_frame = ctk.CTkFrame(self.main_container)
        actions_frame.pack(fill="x", pady=20)
        
        actions_label = ctk.CTkLabel(
            actions_frame,
            text="Actions",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        actions_label.pack(anchor="w", padx=20, pady=10)
        
        button_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        reactivate_button = ctk.CTkButton(
            button_frame,
            text="Request Reactivation",
            height=40,
            command=self.request_reactivation
        )
        reactivate_button.pack(side="left", padx=5)
        
        history_button = ctk.CTkButton(
            button_frame,
            text="View History",
            height=40,
            command=self.view_history
        )
        history_button.pack(side="left", padx=5)
        
        # Status bar
        self.status_bar = ctk.CTkLabel(
            self.main_container,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_bar.pack(side="bottom", fill="x", pady=(20, 0))
    
    def load_license_info(self):
        """Load license information from API"""
        def fetch():
            try:
                response = requests.post(
                    f"{self.api_url}/api/verify-license",
                    json={"license_key": self.license_key, "machine_id": self.machine_id},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.license_info = data.get("license", {})
                    
                    # Update UI in main thread
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
        """Update UI with license information"""
        if not self.license_info:
            return
        
        # Update info labels
        self.info_labels["license_key"].configure(text=self.license_info.get("key", "N/A"))
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
            if remaining_days < 0:
                remaining_days = 0
            self.info_labels["remaining_days"].configure(text=f"{remaining_days} days")
            
            # Update progress bar (assuming max 365 days)
            progress = min(remaining_days / 365, 1.0)
            self.progress_bar.set(progress)
            
            if remaining_days <= 7:
                self.progress_bar.configure(progress_color="red")
            elif remaining_days <= 30:
                self.progress_bar.configure(progress_color="orange")
            else:
                self.progress_bar.configure(progress_color="green")
        else:
            self.info_labels["remaining_days"].configure(text="Lifetime")
            self.progress_bar.set(1.0)
        
        machine_id = self.license_info.get("machine_id", "N/A")
        if machine_id and len(machine_id) > 20:
            machine_id = machine_id[:20] + "..."
        self.info_labels["machine_id"].configure(text=machine_id)
        
        self.status_bar.configure(text="Last updated: " + datetime.now().strftime("%H:%M:%S"), text_color="gray")
    
    def auto_refresh(self):
        """Auto refresh license info every 5 minutes"""
        while self.refresh_running:
            time.sleep(300)  # 5 minutes
            if self.refresh_running:
                self.load_license_info()
    
    def request_reactivation(self):
        """Request license reactivation for new machine"""
        result = messagebox.askyesno(
            "Request Reactivation",
            "This will allow you to use this license on a new machine.\n\nAre you sure you want to proceed?"
        )
        
        if result:
            try:
                response = requests.post(
                    f"{self.api_url}/api/user/reactivate",
                    json={
                        "license_key": self.license_key,
                        "new_machine_id": self.machine_id
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", "License reactivation requested successfully!")
                    self.load_license_info()
                else:
                    messagebox.showerror("Error", "Failed to request reactivation")
            except Exception as e:
                messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def view_history(self):
        """View license access history"""
        try:
            response = requests.get(
                f"{self.api_url}/api/user/history",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                history = data.get("history", [])
                
                # Create history window
                history_window = ctk.CTkToplevel(self.window)
                history_window.title("License History")
                history_window.geometry("800x400")
                
                # Center window
                history_window.update_idletasks()
                x = (history_window.winfo_screenwidth() // 2) - (800 // 2)
                y = (history_window.winfo_screenheight() // 2) - (400 // 2)
                history_window.geometry(f"800x400+{x}+{y}")
                
                # Text widget for history
                text_widget = ctk.CTkTextbox(history_window, wrap="word")
                text_widget.pack(fill="both", expand=True, padx=20, pady=20)
                
                for entry in history:
                    text_widget.insert(
                        "end",
                        f"{entry['created_at']} - {entry['action']}: {entry['details']}\n",
                        "entry"
                    )
                
                text_widget.configure(state="disabled")
            else:
                messagebox.showerror("Error", "Failed to load history")
        except Exception as e:
            messagebox.showerror("Error", f"Connection error: {str(e)}")
    
    def open_settings(self):
        """Open settings window"""
        settings = SettingsWindow(self.window)
        settings.run()
    
    def run(self):
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()
    
    def on_closing(self):
        self.refresh_running = False
        self.window.destroy()