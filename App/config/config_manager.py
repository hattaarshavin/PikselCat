import json
from pathlib import Path

class ConfigManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.config = None
        self.load_config()
    
    def load_config(self):
        """Load application configuration from JSON file"""
        config_path = self.base_dir / "App" / "config" / "app_config.json"
        with open(config_path, 'r') as f:
            self.config = json.load(f)
    
    def get(self, key, default=None):
        """Get configuration value by key"""
        return self.config.get(key, default)
    
    def get_icon_path(self):
        """Get the full path to the application icon"""
        icon_filename = self.get("app_icon", "pixelcat.ico")
        return self.base_dir / "App" / "resource" / "icon" / icon_filename
