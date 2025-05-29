#!/usr/bin/env python3
"""
PikselCat - Entry point for the application
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

def get_base_dir():
    """Get the base directory of PikselCat"""
    return Path(__file__).parent.absolute()

def main():
    """Main entry point for PikselCat"""
    BASE_DIR = get_base_dir()
    
    # Add base directory to Python path
    sys.path.insert(0, str(BASE_DIR))
    
    from App.controller.main_controller import MainController
    
    app = QApplication(sys.argv)
    
    controller = MainController(BASE_DIR)
    controller.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
