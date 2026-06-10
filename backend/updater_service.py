import httpx
from typing import Dict, Any
import os
import json

class UpdaterService:
    
    VERSION = "1.0.0"
    UPDATE_URL = "https://api.github.com/repos/yourusername/license-manager/releases/latest"
    
    @staticmethod
    async def check_update(current_version: str) -> Dict[str, Any]:
        """Check if a new version is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(UpdaterService.UPDATE_URL)
                if response.status_code == 200:
                    release = response.json()
                    latest_version = release.get('tag_name', '').lstrip('v')
                    
                    if UpdaterService._compare_versions(latest_version, current_version) > 0:
                        return {
                            "update_available": True,
                            "version": latest_version,
                            "download_url": release.get('assets', [{}])[0].get('browser_download_url'),
                            "changelog": release.get('body', ''),
                            "release_notes": release.get('body', '')
                        }
                
                return {"update_available": False}
        except Exception as e:
            return {"update_available": False, "error": str(e)}
    
    @staticmethod
    def _compare_versions(version1: str, version2: str) -> int:
        """Compare two version strings"""
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = v1_parts[i] if i < len(v1_parts) else 0
            v2 = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        
        return 0
