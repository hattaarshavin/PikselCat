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
    
    def set(self, key, value):
        """Set configuration value by key and force save for critical data"""
        self.config[key] = value
        # For critical data like validation cache, save immediately but avoid double-save for credits
        if key in ["api_headers", "api_validation_cache"]:
            success = self.save_config()
        elif key == "pixelcut_credits":
            # Don't auto-save credits here - let the caller handle it to avoid conflicts
            pass
    
    def set_nested(self, parent_key, child_key, value):
        """Set nested configuration value"""
        if parent_key not in self.config:
            self.config[parent_key] = {}
        self.config[parent_key][child_key] = value
    
    def save_config(self):
        """Save current configuration to JSON file"""
        try:
            config_path = self.base_dir / "App" / "config" / "app_config.json"
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def save_api_key(self, api_key):
        """Save API key to configuration"""
        try:
            self.set_nested("api_headers", "X-API-KEY", api_key.strip())
            success = self.save_config()
            if success:
                # Force reload to ensure we have latest data
                self.reload_config()
            return success
        except Exception as e:
            print(f"Error saving API key: {e}")
            return False
    
    def get_icon_path(self):
        """Get the full path to the application icon"""
        icon_filename = self.get("app_icon", "pixelcat.ico")
        return self.base_dir / "App" / "resource" / "icon" / icon_filename
    
    def update_pixelcut_credits(self, credits_data):
        """Update pixelcut credits data in configuration"""
        try:
            self.set("pixelcut_credits", credits_data)
            return self.save_config()
        except Exception as e:
            print(f"Error updating pixelcut credits: {e}")
            return False
    
    def get_pixelcut_credits(self):
        """Get pixelcut credits data from configuration"""
        return self.get("pixelcut_credits", {
            "creditsRemaining": 0,
            "credits_remaining": 0,
            "periods": [
                {
                    "credits": 0,
                    "creditsRemaining": 0,
                    "creditsUsed": 0,
                    "periodStart": "0",
                    "periodEnd": "0",
                    "gracePeriodEnd": "0"
                }
            ]
        })
    
    def reload_config(self):
        """Reload configuration from file to get latest data"""
        try:
            self.load_config()
            return True
        except Exception as e:
            print(f"Error reloading config: {e}")
            return False
    
    def get_fresh_data(self, key, default=None):
        """Get fresh data by reloading config first"""
        self.reload_config()
        return self.get(key, default)
