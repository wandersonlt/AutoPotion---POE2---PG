import requests
import os
import sys
import platform
import subprocess
import json
from datetime import datetime

def check_for_updates(api_url, current_version):
    """Check for application updates"""
    try:
        response = requests.get(
            f"{api_url}/api/check-update",
            params={"current_version": current_version},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("update_available"):
                return data
        return None
    except Exception as e:
        print(f"Update check failed: {e}")
        return None

def download_update(url, destination):
    """Download update file"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def install_update(installer_path):
    """Install the update"""
    system = platform.system()
    
    try:
        if system == "Windows":
            # Run installer silently
            subprocess.Popen([installer_path, '/SILENT'], shell=True)
        elif system == "Linux":
            # Make executable and run
            os.chmod(installer_path, 0o755)
            subprocess.Popen([installer_path])
        elif system == "Darwin":  # macOS
            subprocess.Popen(['open', installer_path])
        
        return True
    except Exception as e:
        print(f"Installation failed: {e}")
        return False