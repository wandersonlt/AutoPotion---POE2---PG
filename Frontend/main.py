import customtkinter as ctk
import tkinter.messagebox as messagebox
import requests
import json
import os
import sys
import hashlib
import platform
from datetime import datetime

# Configurar tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LicenseApp:
    def __init__(self):
        self.api_url = "https://autopotion-license-api.onrender.com"
        self.version = "1.0.0"
        self.license_key = None
        self.machine_id = self.get_machine_id()
        self.start()
    
    def get_machine_id(self):
        system = platform.system()
        if system == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                for disk in c.Win32_PhysicalMedia():
                    if disk.SerialNumber:
                        return hashlib.sha256(disk.SerialNumber.encode()).hexdigest()
            except:
                pass
        return hashlib.sha256(platform.node().encode()).hexdigest()
    
    def check_local_license(self):
        license_file = "license.json"
        if os.path.exists(license_file):
            try:
                with open(license_file, 'r') as f:
                    data = json.load(f)
                    return data.get('license_key')
            except:
                pass
        return None
    
    def save_license(self, license_key):
        with open("license.json", 'w') as f:
            json.dump({"license_key": license_key}, f)
        self.license_key = license_key
    
    def verify_license_with_api(self, license_key):
        try:
            response = requests.post(
                f"{self.api_url}/api/verify-license",
                params={"license_key": license_key, "machine_id": self.machine_id},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("valid"):
                    self.save_license(license_key)
                    return True, data.get("license", {})
                else:
                    return False, data.get("message", "Invalid license")
            else:
                return False, f"API error: {response.status_code}"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def start(self):
        local_license = self.check_local_license()
        if local_license:
            valid, result = self.verify_license_with_api(local_license)
            if valid:
                self.open_dashboard()
                return
        
        self.open_login_window()
    
    def open_login_window(self):
        from login_window import LoginWindow
        login = LoginWindow(self.api_url, self.machine_id, self.version)
        license_key = login.run()
        if license_key:
            self.start()
        else:
            sys.exit(0)
    
    def open_dashboard(self):
        from dashboard import Dashboard
        dashboard = Dashboard(self.api_url, self.license_key, self.machine_id, self.version)
        dashboard.run()

if __name__ == "__main__":
    app = LicenseApp()