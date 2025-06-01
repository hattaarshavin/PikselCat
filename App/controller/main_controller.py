from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer
from pathlib import Path
import os

class MainController(QMainWindow):
    def __init__(self, base_dir):
        super().__init__()
        self.BASE_DIR = base_dir
        
        # Enable drag & drop on main window
        self.setAcceptDrops(True)
        
        # Import dependencies
        from App.config.config_manager import ConfigManager
        from App.helpers._ui_helper import UIHelper
        from App.helpers._status_helper import StatusHelper
        self.config_manager = ConfigManager(base_dir)
        self.ui_helper = UIHelper()
        self.status_helper = StatusHelper()
        
        # Set status helper reference in ui helper for error reporting
        self.ui_helper.set_status_helper(self.status_helper)
          # Controllers for managing status updates
        self.dnd_handler = None
        self.work_handler = None
        self.actions_controller = None
        
        # Use UI helper to load main UI asynchronously
        self.ui_helper.load_main_ui_async(
            self.BASE_DIR, 
            "main_window.ui",
            self.on_ui_loaded,
            self.on_ui_error
        )
    def on_ui_loaded(self, ui_window):
        """Handle UI loaded event - runs in main thread"""
        if ui_window:
            # Copy the centralwidget from loaded UI to our window
            centralwidget = ui_window.centralWidget()
            if centralwidget:
                self.setCentralWidget(centralwidget)
                
                # Load widgets after UI is set
                QTimer.singleShot(0, self.load_widgets)
                
            # Copy menubar and statusbar if they exist
            if ui_window.menuBar():
                self.setMenuBar(ui_window.menuBar())
            if ui_window.statusBar():
                self.setStatusBar(ui_window.statusBar())
                # Set status bar reference in status helper
                self.status_helper.set_status_bar(self.statusBar())
                # Set initial status message
                self.status_helper.show_ready("Application ready")
            
            # Set window properties
            self.setWindowTitle(self.config_manager.get("app_name"))
            self.resize(800, 600)
            self.center_on_screen()
            
            # Add the program icon
            icon_path = self.config_manager.get_icon_path()
            if icon_path.exists():
                window_icon = QIcon(str(icon_path))
                self.setWindowIcon(window_icon)
        
        # Load styles after UI is ready
        QTimer.singleShot(0, self.load_styles)
        
    def on_ui_error(self, error_message):
        """Handle UI loading error"""
        from PySide6.QtWidgets import QLabel
        fallback_label = QLabel(f"UI Loading Error: {error_message}")
        fallback_label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(fallback_label)        # Update status bar if available
        if self.statusBar():
            self.statusBar().showMessage(f"Error: {error_message}")
    def load_styles(self):
        """Load CSS styles from main_style.css"""
        try:
            css_content = self.ui_helper.load_css_file(self.BASE_DIR, "main_style.css")
            if css_content:
                self.setStyleSheet(css_content)        
        except Exception as e:
            print(f"Error loading styles: {e}")
            self.status_helper.show_error("Failed to load UI styles")
    
    def load_widgets(self):
        """Load and integrate the widget UIs using UI helper"""
        from PySide6.QtWidgets import QWidget
        try:

            
            # Find the container widgets
            central_widget = self.centralWidget()
            if not central_widget:
                return
                
            actions_container = central_widget.findChild(QWidget, "actionsContainer")
            statistics_container = central_widget.findChild(QWidget, "statisticsContainer")
            workspace_container = central_widget.findChild(QWidget, "workspaceContainer")
            
            # Load actions widget using UI helper
            if actions_container:
                actions_widget = self.ui_helper.load_widget_safely(
                    self.BASE_DIR, "actions.ui", actions_container
                )
                if actions_widget:
                    from App.controller.actions import ActionsController
                    self.actions_controller = ActionsController(actions_widget, self.status_helper)
                      # Pass config_manager to actions controller
                    self.actions_controller.set_config_manager(self.config_manager)
                    
                    # Initialize worker variable for processing
                    self.processing_worker = None
                    
                    # Connect run/stop signals directly to methods
                    self.actions_controller.run_clicked.connect(self.start_processing)
                    self.actions_controller.stop_clicked.connect(self.stop_processing)
                    
                    # Setup settings button icon
                    from PySide6.QtWidgets import QPushButton
                    import qtawesome as qta
                    settings_btn = actions_widget.findChild(QPushButton, "settingsButton")
                    if settings_btn:
                        settings_icon = qta.icon('fa6s.gear', color='white')
                        settings_btn.setIcon(settings_icon)
              # Load statistics widget using UI helper
            if statistics_container:
                stats_widget = self.ui_helper.load_widget_safely(
                    self.BASE_DIR, "statistics.ui", statistics_container
                )
                if stats_widget:
                    # Initialize statistics controller
                    from App.controller.statistics import StatisticsController
                    self.statistics_controller = StatisticsController(self.config_manager)
                    self.statistics_controller.setup_ui_connections(stats_widget)
            
            # Load workspace widget using UI helper
            if workspace_container:
                workspace_widget = self.ui_helper.load_widget_safely(
                    self.BASE_DIR, "workspace.ui", workspace_container
                )
                if workspace_widget:
                    # TODO: Initialize workspace controller if needed
                    pass

                    # Load DnD area inside workspace using UI helper
                    dnd_container = workspace_widget.findChild(QWidget, "dndContainer")
                    if dnd_container:
                        self.ui_helper.load_dnd_widget_safely(
                            self.BASE_DIR, 
                            dnd_container, 
                            workspace_widget,
                            self.init_dnd_handler
                        )
        except Exception as e:
            print(f"Error loading widgets: {e}")
            self.status_helper.show_error(f"Failed to load widgets: {e}")    
    def init_dnd_handler(self, dnd_widget, workspace_widget, work_area_widget):
        """Initialize DnD handler safely"""
        try:
            from App.controller.dnd_handler import DndHandler
            from PySide6.QtWidgets import QPushButton
              # Find the buttons in the DnD widget
            open_files_btn = dnd_widget.findChild(QPushButton, "openFilesButton")
            open_folder_btn = dnd_widget.findChild(QPushButton, "openFolderButton")
            
            if open_files_btn and open_folder_btn:
                # Create work handler first with config_manager
                from App.controller.work_handler import WorkHandler
                self.work_handler = WorkHandler(
                    workspace_widget, 
                    work_area_widget, 
                    self.status_helper,
                    self.config_manager
                )
                
                # Create DnD handler and set work handler reference
                self.dnd_handler = DndHandler(
                    dnd_widget, 
                    workspace_widget, 
                    open_files_btn, 
                    open_folder_btn,
                    self.status_helper
                )
                
                # Connect the handlers
                self.dnd_handler.set_work_handler(self.work_handler)
                
                # Connect work handler signals if needed
                self.work_handler.files_cleared.connect(lambda: self.dnd_handler.files_loaded.emit([]))
                
                self.status_helper.show_ready("Drag & drop ready")
            else:
                print("Error: Could not find DnD buttons")
                self.status_helper.show_error("Could not find DnD buttons")
            
        except Exception as e:
            print(f"Error initializing DnD handler: {e}")
            self.status_helper.show_error(f"DnD handler initialization failed: {e}")
    
    def center_on_screen(self):
        """Center the window on screen"""
        screen = QApplication.primaryScreen().availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

    def start_processing(self):
        """Start the Pixelcut processing workflow"""
        try:
            # Get loaded files from work handler            
            if not self.work_handler:
                self.status_helper.show_error("Work handler not initialized")
                return
                
            files = self.work_handler.get_loaded_files()
            if not files:
                self.status_helper.show_error("No files loaded for processing")
                return
            
            # Get file widgets from work handler (it's a list, not dict)
            file_widgets = self.work_handler.file_widgets
            if not file_widgets:
                self.status_helper.show_error("No file widgets available")
                return
              
            # Get selected action from work handler
            selected_action = self.work_handler.get_selected_action()
            if not selected_action:
                self.status_helper.show_error("No action selected")
                return
            
            # Get output destination from actions controller
            output_path = self.actions_controller.get_output_destination()
            if not output_path:
                self.status_helper.show_error("No output destination selected")
                return
            
            # Create and start the processor worker
            from App.helpers.pixelcut_processor import PixelcutProcessorWorker
            self.processing_worker = PixelcutProcessorWorker(
                self.config_manager, 
                files, 
                selected_action, 
                output_path
            )
            
            # Connect signals
            self.processing_worker.file_processing_started.connect(self.on_file_processing_started)
            self.processing_worker.file_processed.connect(self.on_file_processed)
            self.processing_worker.progress_updated.connect(self.on_progress_updated)
            self.processing_worker.processing_completed.connect(self.on_processing_completed)
            self.processing_worker.processing_cancelled.connect(self.on_processing_cancelled)
            self.processing_worker.error_occurred.connect(self.on_processing_error)
            
            # Set all file widgets to processing state - file_widgets is a list
            for widget in file_widgets:
                widget.set_processing_state("idle")
            
            # Start processing
            self.processing_worker.start()
            self.status_helper.show_status(f"Processing {len(files)} files with {selected_action}...", self.status_helper.PRIORITY_NORMAL)
            
            # Update actions controller to show stop button
            if hasattr(self.actions_controller, 'set_processing_state'):
                self.actions_controller.set_processing_state(True)
            
        except Exception as e:
            # Print to console for debugging, don't show in status bar
            print(f"Failed to start processing: {str(e)}")
            print(f"Exception type: {type(e)}")
            print(f"Work handler type: {type(self.work_handler.file_widgets) if self.work_handler else 'None'}")
            if self.work_handler and hasattr(self.work_handler, 'file_widgets'):
                print(f"File widgets content: {self.work_handler.file_widgets}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            
    def stop_processing(self):
        """Stop the current processing workflow"""
        try:
            if hasattr(self, 'processing_worker') and self.processing_worker:
                if self.processing_worker.isRunning():
                    self.processing_worker.cancel()
                    self.status_helper.show_warning("Stopping processing...")
                      # Reset file widgets to idle state - file_widgets is a list
                    if self.work_handler and hasattr(self.work_handler, 'file_widgets'):
                        for widget in self.work_handler.file_widgets:
                            widget.set_processing_state("idle")
                    
                    # Set completed state - both buttons disabled
                    if hasattr(self.actions_controller, 'set_processing_completed_state'):
                        self.actions_controller.set_processing_completed_state()
                else:
                    self.status_helper.show_warning("No active processing to stop")
            else:
                self.status_helper.show_warning("No processing to stop")
        except Exception as e:
            self.status_helper.show_error(f"Failed to stop processing: {str(e)}")
    
    def on_file_processing_started(self, file_path):
        """Handle when a file starts processing"""
        try:
            if self.work_handler and hasattr(self.work_handler, 'file_widgets'):
                # Find widget by file path since file_widgets is a list
                for widget in self.work_handler.file_widgets:
                    if widget.get_file_path() == file_path:
                        widget.set_processing_state("processing")
                        print(f"Started processing: {file_path}")
                        break
        except Exception as e:
            print(f"Error updating file processing state: {e}")
    
    def on_file_processed(self, input_file, output_file, success):
        """Handle when a file is processed"""
        try:
            if self.work_handler and hasattr(self.work_handler, 'file_widgets'):
                # Find widget by file path since file_widgets is a list
                for widget in self.work_handler.file_widgets:
                    if widget.get_file_path() == input_file:
                        if success:
                            widget.set_processing_state("success")
                            print(f"Successfully processed: {input_file} -> {output_file}")
                        else:
                            widget.set_processing_state("error")
                            print(f"Failed to process: {input_file}")
                        break
        except Exception as e:
            print(f"Error updating file processed state: {e}")
    
    def on_progress_updated(self, progress, message):
        """Handle progress updates"""
        try:
            # Only update status bar for important milestones, not every progress update
            if progress % 25 == 0 or progress >= 100:  # Only at 0%, 25%, 50%, 75%, 100%
                self.status_helper.show_status(message, self.status_helper.PRIORITY_NORMAL)
            else:
                print(f"Progress: {progress}% - {message}")
        except Exception as e:
            print(f"Error updating progress: {e}")
    def on_processing_completed(self, processed_count, failed_count):
        """Handle processing completion"""
        try:
            message = f"Processing completed: {processed_count} successful, {failed_count} failed"
            if failed_count == 0:
                self.status_helper.show_success(message)
            else:
                self.status_helper.show_warning(message)
            
            # Set completed state - both buttons disabled until new files loaded
            if hasattr(self.actions_controller, 'set_processing_completed_state'):
                self.actions_controller.set_processing_completed_state()
            
            # Clean up worker
            if hasattr(self, 'processing_worker'):
                self.processing_worker = None
        except Exception as e:
            print(f"Error handling processing completion: {e}")
    
    def on_processing_cancelled(self):
        """Handle processing cancellation"""
        try:
            self.status_helper.show_warning("Processing cancelled")
            
            # Set completed state - both buttons disabled until new files loaded
            if hasattr(self.actions_controller, 'set_processing_completed_state'):
                self.actions_controller.set_processing_completed_state()
            
            # Clean up worker
            if hasattr(self, 'processing_worker'):
                self.processing_worker = None
        except Exception as e:
            print(f"Error handling processing cancellation: {e}")
    
    def on_processing_error(self, error_message):
        """Handle processing errors"""
        try:
            self.status_helper.show_error(f"Processing error: {error_message}")
            
            # Update actions controller
            if hasattr(self.actions_controller, 'set_processing_state'):
                self.actions_controller.set_processing_state(False)
            
            # Clean up worker
            if hasattr(self, 'processing_worker'):
                self.processing_worker = None
        except Exception as e:
            print(f"Error handling processing error: {e}")
