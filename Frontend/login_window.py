import customtkinter as ctk
import requests
import json
import os
import threading
import traceback

class LoginWindow:
    def __init__(self, api_url, machine_id, version):
        self.api_url = api_url
        self.machine_id = machine_id
        self.version = version
        self.result = None
        
        self.window = ctk.CTk()
        self.window.title("License Manager - Login")
        self.window.geometry("550x550")
        self.window.resizable(False, False)
        
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.window.winfo_screenheight() // 2) - (550 // 2)
        self.window.geometry(f"550x550+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="License Manager",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Enter your license key to continue",
            font=ctk.CTkFont(size=14)
        )
        subtitle_label.pack(pady=(0, 30))
        
        license_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        license_frame.pack(fill="x", pady=10)
        
        license_label = ctk.CTkLabel(
            license_frame,
            text="License Key",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        license_label.pack(anchor="w", pady=(0, 5))
        
        self.license_entry = ctk.CTkEntry(
            license_frame,
            placeholder_text="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.license_entry.pack(fill="x")
        self.license_entry.insert(0, "CEJ0G-14EEA-0U1WU-PL9VR-BCHBV")
        
        machine_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        machine_frame.pack(fill="x", pady=(20, 10))
        
        machine_label = ctk.CTkLabel(
            machine_frame,
            text="Machine ID",
            font=ctk.CTkFont(size=12)
        )
        machine_label.pack(anchor="w")
        
        machine_id_label = ctk.CTkLabel(
            machine_frame,
            text=self.machine_id[:30] + "...",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        machine_id_label.pack(anchor="w")
        
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=30)
        
        self.activate_button = ctk.CTkButton(
            buttons_frame,
            text="Activate License",
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.activate_license
        )
        self.activate_button.pack(fill="x", pady=5)
        
        self.buy_button = ctk.CTkButton(
            buttons_frame,
            text="Buy License",
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            border_width=2,
            command=self.open_buy_page
        )
        self.buy_button.pack(fill="x", pady=5)
        
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color="green"
        )
        self.status_label.pack(pady=20)
        
        version_label = ctk.CTkLabel(
            main_frame,
            text=f"Version {self.version}",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        version_label.pack(side="bottom", pady=10)
    
    def activate_license(self):
        self.activate_button.configure(state="disabled")
        self.buy_button.configure(state="disabled")
        self.status_label.configure(text="Verifying...", text_color="orange")
        
        license_key = self.license_entry.get().strip().upper()
        
        if not license_key:
            self.status_label.configure(text="Please enter a license key", text_color="red")
            self.activate_button.configure(state="normal")
            self.buy_button.configure(state="normal")
            return
        
        def verify():
            try:
                print(f"🔍 Verificando licença: {license_key}")
                print(f"📍 API: {self.api_url}")
                
                response = requests.post(
                    f"{self.api_url}/api/verify-license",
                    params={"license_key": license_key, "machine_id": self.machine_id},
                    timeout=15
                )
                
                print(f"📡 Status: {response.status_code}")
                print(f"📄 Resposta: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("valid"):
                        with open("license.json", "w") as f:
                            json.dump({"license_key": license_key}, f)
                        
                        self.window.after(0, lambda: self.status_label.configure(text="Success!", text_color="green"))
                        self.window.after(1500, self.close_window)
                        self.result = license_key
                    else:
                        self.window.after(0, lambda: self.status_label.configure(text=data.get("message", "Invalid"), text_color="red"))
                        self.window.after(0, lambda: self.activate_button.configure(state="normal"))
                        self.window.after(0, lambda: self.buy_button.configure(state="normal"))
                else:
                    self.window.after(0, lambda: self.status_label.configure(text=f"Error: {response.status_code}", text_color="red"))
                    self.window.after(0, lambda: self.activate_button.configure(state="normal"))
                    self.window.after(0, lambda: self.buy_button.configure(state="normal"))
            except Exception as e:
                print(f"❌ ERRO: {e}")
                traceback.print_exc()
                self.window.after(0, lambda: self.status_label.configure(text=f"Error: {str(e)}", text_color="red"))
                self.window.after(0, lambda: self.activate_button.configure(state="normal"))
                self.window.after(0, lambda: self.buy_button.configure(state="normal"))
        
        threading.Thread(target=verify, daemon=True).start()
    
    def open_buy_page(self):
        import webbrowser
        webbrowser.open(f"{self.api_url}/buy")
    
    def close_window(self):
        self.window.quit()
        self.window.destroy()
    
    def run(self):
        self.window.mainloop()
        return self.result