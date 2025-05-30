from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QSpacerItem, QSizePolicy, QComboBox, QComboBox
from PySide6.QtCore import QObject, Signal, Qt
import qtawesome as qta
import os
from .loaded_item_widget import LoadedItemWidget
from App.helpers._url_helper import UrlHelper

class WorkHandler(QObject):
    """Handler for work area operations and file processing"""
    # Signals for communication with other components
    files_cleared = Signal()
    
    def __init__(self, workspace_widget: QWidget, work_area_widget: QWidget, status_helper, config_manager=None):
        super().__init__()
        self.workspace_widget = workspace_widget
        self.work_area_widget = work_area_widget
        self.status_helper = status_helper
        self.config_manager = config_manager
        self.loaded_files = []
        self.file_widgets = []  # Store references to LoadedItemWidget instances
        
        # Get the stacked widget for switching between DnD and Work Area
        self.stacked_widget = workspace_widget.findChild(QStackedWidget, "stackedWidget")
        
        self.setup_ui()
        self.setup_connections()
    def setup_ui(self):
        """Setup the work area UI elements with icons"""
        if self.work_area_widget:
            
            # Find and set icon for clear button (using X icon instead of trash)
            clear_btn = self.work_area_widget.findChild(QPushButton, "clearFilesButton")
            if clear_btn:                
                clear_icon = qta.icon('fa6s.xmark', color='white')
                clear_btn.setIcon(clear_icon)
            
            # Find and set icon for WhatsApp button
            whatsapp_btn = self.work_area_widget.findChild(QPushButton, "whatsappButton")
            if whatsapp_btn:
                whatsapp_icon = qta.icon('fa6b.whatsapp', color='white')
                whatsapp_btn.setIcon(whatsapp_icon)
            
            # Set icons for cost information labels
            estimated_cost_icon = self.work_area_widget.findChild(QLabel, "estimatedCostIcon")
            if estimated_cost_icon:
                cost_icon = qta.icon('fa6s.calculator', color='#ff7f36')
                estimated_cost_icon.setPixmap(cost_icon.pixmap(16, 16))
            
            remaining_credit_icon = self.work_area_widget.findChild(QLabel, "remainingCreditIcon")
            if remaining_credit_icon:
                credit_icon = qta.icon('fa6s.wallet', color='#ff7f36')
                remaining_credit_icon.setPixmap(credit_icon.pixmap(16, 16))
            
            # Initialize cost calculation display
            self.update_cost_calculation()
    
    def setup_connections(self):
        """Setup work area button connections"""
        if self.work_area_widget:
            clear_btn = self.work_area_widget.findChild(QPushButton, "clearFilesButton")
            if clear_btn:
                clear_btn.clicked.connect(self.clear_files)
            
            # Connect WhatsApp button
            whatsapp_btn = self.work_area_widget.findChild(QPushButton, "whatsappButton")
            if whatsapp_btn:
                whatsapp_btn.clicked.connect(self.open_whatsapp)
                   # Connect combobox change to update cost calculation
            action_combo = self.work_area_widget.findChild(QComboBox, "actionComboBox")
            if action_combo:
                action_combo.currentTextChanged.connect(self.update_cost_calculation)
    
    def load_files(self, files):
        """Load files into work area with two-stage loading process"""
        self.loaded_files = files
        
        # Stage 1 is already complete (file validation), now do Stage 2 (widget creation)
        self.start_widget_creation()
    def start_widget_creation(self):
        """Start the widget creation process with progress tracking"""
        if not self.loaded_files:
            self.switch_to_work_area()
            return
            
        # Check if we already have a progress dialog from the validation stage
        if not hasattr(self, 'progress_dialog') or not self.progress_dialog:
            # Create progress dialog for widget creation stage
            from App.gui.dialogs.progress_dialog import ProgressDialog
            
            self.progress_dialog = ProgressDialog(self.work_area_widget)
            self.progress_dialog.set_stage("widgets", 0)
            self.progress_dialog.cancel_requested.connect(self.cancel_widget_creation)
            self.progress_dialog.show()
        else:
            # Progress dialog exists from validation stage - just update it
            self.progress_dialog.set_stage("widgets", 0)
            # Connect cancel signal if not already connected
            try:
                self.progress_dialog.cancel_requested.connect(self.cancel_widget_creation)
            except:
                pass  # Already connected
        
        # Clear existing file widgets first
        scroll_area = self.work_area_widget.findChild(QWidget, "scrollAreaWidgetContents")
        if scroll_area:
            file_list_layout = scroll_area.findChild(QVBoxLayout, "fileListLayout")
            if file_list_layout:
                self.clear_file_widgets(file_list_layout)
        
        # Create widget creation manager
        from App.helpers.widget_loader_worker import WidgetCreationManager
        
        self.widget_manager = WidgetCreationManager(self)
        self.widget_manager.progress_updated.connect(self.on_widget_progress_updated)
        self.widget_manager.widget_created.connect(self.on_widget_created)
        self.widget_manager.loading_completed.connect(self.on_widget_creation_completed)
        self.widget_manager.loading_cancelled.connect(self.on_widget_creation_cancelled)
        
        # Start widget creation
        self.widget_manager.start_creation(self.loaded_files, scroll_area)
        
        # Switch to work area immediately
        self.switch_to_work_area()
    
    def on_widget_progress_updated(self, progress, status):
        """Handle progress updates from widget creation"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.set_value(progress)
            self.progress_dialog.set_status(status)
    def on_widget_created(self, widget):
        """Handle individual widget creation"""
        # Connect the remove signal
        widget.remove_requested.connect(self.remove_file)
        
        # Add widget to layout
        scroll_area = self.work_area_widget.findChild(QWidget, "scrollAreaWidgetContents")
        if scroll_area:
            file_list_layout = scroll_area.findChild(QVBoxLayout, "fileListLayout")
            if file_list_layout:
                # Remove any existing stretch before adding widget
                if file_list_layout.count() > 0:
                    last_item = file_list_layout.itemAt(file_list_layout.count() - 1)
                    if last_item and last_item.spacerItem():
                        file_list_layout.removeItem(last_item)
                
                self.file_widgets.append(widget)
                file_list_layout.addWidget(widget)
                
                # Update cost calculation in real-time as widgets are created
                self.update_cost_calculation()
    
    def remove_file(self, file_path):
        """Remove a specific file from the loaded files"""
        if file_path in self.loaded_files:
            # Remove from loaded files list
            self.loaded_files.remove(file_path)
            
            # Find and remove the corresponding widget
            widget_to_remove = None
            for widget in self.file_widgets:
                if widget.get_file_path() == file_path:
                    widget_to_remove = widget
                    break
            
            if widget_to_remove:
                # Remove from layout and delete widget
                self.file_widgets.remove(widget_to_remove)
                widget_to_remove.setParent(None)
                widget_to_remove.deleteLater()
                  # Update header
                self.update_work_area_header()
                self.update_cost_calculation()
                
                # If no files left, switch back to DnD area
                if not self.loaded_files:
                    self.switch_to_dnd_area()
                    self.files_cleared.emit()
                    self.status_helper.show_ready("Ready for new files")
                else:
                    self.status_helper.show_status(f"Removed file. {len(self.loaded_files)} files remaining.", self.status_helper.PRIORITY_NORMAL)
    
    def on_widget_creation_completed(self, widgets):
        """Handle completion of widget creation"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Add final stretch to push widgets to the top
        scroll_area = self.work_area_widget.findChild(QWidget, "scrollAreaWidgetContents")
        if scroll_area:
            file_list_layout = scroll_area.findChild(QVBoxLayout, "fileListLayout")
            if file_list_layout:
                file_list_layout.addStretch()
          # Update header with final counts
        self.update_work_area_header()
        self.update_cost_calculation()
        
        self.status_helper.show_success(f"Created {len(widgets)} file widgets")
        
        # Clean up widget manager
        if hasattr(self, 'widget_manager'):
            self.widget_manager.deleteLater()
            self.widget_manager = None
    
    def on_widget_creation_cancelled(self):
        """Handle cancellation of widget creation"""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.status_helper.show_status("Widget creation cancelled", self.status_helper.PRIORITY_NORMAL)
        
        # Clean up widget manager
        if hasattr(self, 'widget_manager'):
            self.widget_manager.deleteLater()
            self.widget_manager = None
    def cancel_widget_creation(self):
        """Cancel the widget creation operation"""
        if hasattr(self, 'widget_manager') and self.widget_manager:
            self.widget_manager.cancel()
    
    def clear_files(self):
        """Clear all loaded files and switch back to DnD area"""
        # Cancel any ongoing widget creation
        if hasattr(self, 'widget_manager') and self.widget_manager:
            self.widget_manager.cancel()
        
        # Close any open progress dialog
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # Clear file data and widgets
        self.loaded_files = []
        
        # Clear the UI
        scroll_area = self.work_area_widget.findChild(QWidget, "scrollAreaWidgetContents")
        if scroll_area:
            file_list_layout = scroll_area.findChild(QVBoxLayout, "fileListLayout")
            if file_list_layout:
                self.clear_file_widgets(file_list_layout)
        self.switch_to_dnd_area()
        self.files_cleared.emit()
        
        # Update cost calculation after clearing files
        self.update_cost_calculation()
        
        self.status_helper.show_ready("Ready for new files")
    def switch_to_work_area(self):
        """Switch to work area view"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(1)  # Work area is at index 1
    
    def switch_to_dnd_area(self):
        """Switch to DnD area view"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)  # DnD area is at index 0
    
    def update_work_area_header(self):
        """Update the work area header with file and folder counts"""
        title_label = self.work_area_widget.findChild(QLabel, "workAreaTitle")
        
        if self.loaded_files:
            # Count unique folders
            folders = set()
            for file_path in self.loaded_files:
                folder_path = os.path.dirname(file_path)
                if folder_path:
                    folders.add(folder_path)
            
            file_count = len(self.loaded_files)
            folder_count = len(folders)
            
            # Update title with counts
            if title_label:
                title_text = f"{file_count} files loaded ({folder_count} folder{'s' if folder_count != 1 else ''})"
                title_label.setText(title_text)
        else:
            # No files loaded
            if title_label:
                title_label.setText("Work Area")
    def clear_file_widgets(self, layout):
        """Clear all existing file widgets from the layout"""
        # Remove widgets from layout and delete them
        while layout.count():
            child = layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
            # Handle spacers and other layout items
            elif child.spacerItem():
                # Spacer items don't need special cleanup
                pass
        
        # Clear our widget references
        self.file_widgets.clear()
    
    def get_loaded_files(self):
        """Get the currently loaded files"""
        return self.loaded_files
    
    def get_loaded_files_count(self):
        """Get the count of loaded files"""
        return len(self.loaded_files)
    
    def get_cost_per_action(self, action_text):
        """Get cost per file for the selected action"""
        if "Upscale" in action_text:
            return 10  # 10 credit per file for upscale
        elif "Remove Bg" in action_text:
            return 5   # 5 credit per file for remove background        
        else:
            return 0   # Default cost
    def update_cost_calculation(self):
        """Update estimated cost based on current action and widget count (real-time)"""
        if not self.work_area_widget:
            return
            
        action_combo = self.work_area_widget.findChild(QComboBox, "actionComboBox")
        cost_label = self.work_area_widget.findChild(QLabel, "estimatedCostLabel")
        
        if action_combo and cost_label:
            current_action = action_combo.currentText()
            # Use only actual widget count for true real-time calculation
            widget_count = len(self.file_widgets)
            cost_per_file = self.get_cost_per_action(current_action)
            current_cost = widget_count * cost_per_file
            
            if widget_count > 0:
                # Show cost for widgets that are actually created
                cost_label.setText(f"Estimated cost: {current_cost} Credit for {widget_count} files")
            else:
                # No widgets created yet
                cost_label.setText("Estimated cost: 0 Credit for 0 files")
    
    def open_whatsapp(self):
        """Open WhatsApp group using URL from config"""
        if self.config_manager:
            whatsapp_url = self.config_manager.get("whatsapp")
            
            if whatsapp_url:
                success = UrlHelper.open_whatsapp(whatsapp_url, self.work_area_widget)
                if success:
                    self.status_helper.show_status("Opening WhatsApp group...", self.status_helper.PRIORITY_NORMAL)
                else:
                    self.status_helper.show_status("Failed to open WhatsApp link", self.status_helper.PRIORITY_HIGH)
            else:
                self.status_helper.show_status("WhatsApp URL not configured", self.status_helper.PRIORITY_HIGH)
        else:
            self.status_helper.show_status("Configuration not available", self.status_helper.PRIORITY_HIGH)