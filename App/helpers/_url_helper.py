import webbrowser
from PySide6.QtWidgets import QMessageBox

class UrlHelper:
    @staticmethod
    def open_url(url, parent=None):
        """Open URL in default browser with error handling"""
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            if parent:
                QMessageBox.warning(parent, "Error", f"Could not open URL: {str(e)}")
            return False
    
    @staticmethod
    def open_whatsapp(url, parent=None):
        """Open WhatsApp URL specifically"""
        return UrlHelper.open_url(url, parent)
    
    @staticmethod
    def open_repository(url, parent=None):
        """Open repository URL specifically"""
        return UrlHelper.open_url(url, parent)
