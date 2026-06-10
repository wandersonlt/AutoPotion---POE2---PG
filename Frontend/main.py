import customtkinter as ctk
import tkinter.messagebox as messagebox
import requests
import json
import os
import sys
import hashlib
import platform
from datetime import datetime
from Frontend.login_window import LoginWindow
from dashboard import Dashboard
from updater import check_for_updates
from .database import engine, get_db, Base
from .models import User, License, Plan
from .auth import AuthHandler
from .license_service import LicenseService

class LicenseApp:
    def __init__(self):
        # Configure theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # API configuration
        self.api_url = os.getenv("API_URL", "https://your-app.onrender.com")
        self.version = "1.0.0"
        
        # License data
        self.license_key = None
        self.machine_id = self.get_machine_id()
        
        # Start application
        self.start()
    
    def get_machine_id(self):
        """Generate unique machine ID"""
        system = platform.system()
        
        if system == "Windows":
            import wmi
            c = wmi.WMI()
            for disk in c.Win32_PhysicalMedia():
                if disk.SerialNumber:
                    return hashlib.sha256(disk.SerialNumber.encode()).hexdigest()
        elif system == "Linux":
            import subprocess
            result = subprocess.run(['cat', '/var/lib/dbus/machine-id'], 
                                  capture_output=True, text=True)
            return hashlib.sha256(result.stdout.strip().encode()).hexdigest()
        elif system == "Darwin":  # macOS
            import subprocess
            result = subprocess.run(['ioreg', '-l'], capture_output=True, text=True)
            return hashlib.sha256(result.stdout.encode()).hexdigest()
        
        # Fallback
        return hashlib.sha256(platform.node().encode()).hexdigest()
    
    def check_local_license(self):
        """Check if license is stored locally"""
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
        """Save license locally"""
        with open("license.json", 'w') as f:
            json.dump({"license_key": license_key}, f)
        self.license_key = license_key
    
    def verify_license_with_api(self, license_key):
        """Verify license with backend API"""
        try:
            response = requests.post(
                f"{self.api_url}/api/verify-license",
                json={"license_key": license_key, "machine_id": self.machine_id},
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
                return False, "API error"
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def start(self):
        """Start the application"""
        # Check for updates first
        update_info = check_for_updates(self.api_url, self.version)
        if update_info and update_info.get("update_available"):
            response = messagebox.askyesno(
                "Update Available",
                f"Version {update_info['version']} is available!\n\nChangelog:\n{update_info.get('changelog', '')}\n\nDownload and install now?"
            )
            if response:
                # Download and install update
                import webbrowser
                webbrowser.open(update_info['download_url'])
                sys.exit(0)
        
        # Check local license
        local_license = self.check_local_license()
        if local_license:
            # Verify with API
            valid, result = self.verify_license_with_api(local_license)
            if valid:
                # Open dashboard
                dashboard = Dashboard(self.api_url, local_license, self.machine_id, self.version)
                dashboard.run()
                return
        
        # Show login window
        login_window = LoginWindow(self.api_url, self.machine_id, self.version)
        license_key = login_window.run()
        
        if license_key:
            self.start()
        else:
            sys.exit(0)

if __name__ == "__main__":
    app = LicenseApp()