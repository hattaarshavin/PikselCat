from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, Signal
import qtawesome as qta

class ActionsController(QObject):
    # Signals for when buttons are clicked
    run_clicked = Signal()
    stop_clicked = Signal()
    
    def __init__(self, actions_widget: QWidget):
        super().__init__()
        self.actions_widget = actions_widget
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the UI elements with icons"""
        if self.actions_widget:
            # Find the run button
            run_button = self.actions_widget.findChild(QWidget, "runButton")
            if run_button:
                # Add play icon using QtAwesome fa6s
                play_icon = qta.icon('fa6s.play', color='white')
                run_button.setIcon(play_icon)
            
            # Find the stop button
            stop_button = self.actions_widget.findChild(QWidget, "stopButton")
            if stop_button:
                # Add stop icon using QtAwesome fa6s
                stop_icon = qta.icon('fa6s.stop', color='white')
                stop_button.setIcon(stop_icon)
    
    def connect_signals(self):
        """Connect button signals to slots"""
        if self.actions_widget:
            run_button = self.actions_widget.findChild(QWidget, "runButton")
            if run_button:
                run_button.clicked.connect(self.on_run_clicked)
            
            stop_button = self.actions_widget.findChild(QWidget, "stopButton")
            if stop_button:
                stop_button.clicked.connect(self.on_stop_clicked)
    def on_run_clicked(self):
        """Handle run button click"""
        print("Run button clicked!")
        self.set_running_state(True)
        self.run_clicked.emit()
    
    def on_stop_clicked(self):
        """Handle stop button click"""
        print("Stop button clicked!")
        self.set_running_state(False)
        self.stop_clicked.emit()
    
    def set_running_state(self, is_running: bool):
        """Set the state of buttons based on running status"""
        if self.actions_widget:
            run_button = self.actions_widget.findChild(QWidget, "runButton")
            stop_button = self.actions_widget.findChild(QWidget, "stopButton")
            
            if run_button and stop_button:
                if is_running:
                    # When running: disable run button, enable stop button
                    run_button.setEnabled(False)
                    stop_button.setEnabled(True)
                else:
                    # When not running: enable run button, disable stop button
                    run_button.setEnabled(True)
                    stop_button.setEnabled(False)