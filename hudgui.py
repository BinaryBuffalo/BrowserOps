import sys
import json
from pathlib import Path
import subprocess
import psutil  # For PID validation
import shutil

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QGridLayout,
    QVBoxLayout, QHBoxLayout, QScrollArea, QMessageBox, QComboBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QFileSystemWatcher

# Importing additional modules for PID retrieval
try:
    import pygetwindow as gw
    import win32process
except ImportError:
    print("Required modules 'pygetwindow' and 'pywin32' are not installed.")
    print("Install them using pip:")
    print("pip install pygetwindow pywin32")
    sys.exit(1)


def get_pid_from_taskbar_label(label):
    """
    Retrieves the PID of a window based on its taskbar label.
    """
    windows = gw.getAllWindows()

    for window in windows:
        # Check if the window title contains the label
        if label.lower() in window.title.lower():
            try:
                hwnd = window._hWnd  # Get the window handle
                # Get the process ID from the window handle using win32process
                pid = win32process.GetWindowThreadProcessId(hwnd)[1]
                return pid
            except Exception as e:
                print(f"Error getting PID for label '{label}': {e}")
                continue

    return None  # no matching window is found


class InstanceWidget(QWidget): # AI rewrote this cause mine was messy thanks gemini :)
    def __init__(self, instance_number, snapshot_path, pid=None, parent=None):
        super().__init__(parent)
        self.instance_number = instance_number
        self.snapshot_path = snapshot_path
        self.pid = pid  # Initialize PID from instances.json
        self.init_ui()
        self.retrieve_pid_if_needed()  # Fetch PID if not provided

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Screenshot Label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setFixedSize(400, 250)  # Set a fixed size for consistency
        self.update_image()
        layout.addWidget(self.image_label)

        # Access Button
        self.access_button = QPushButton("Access")
        self.access_button.clicked.connect(self.access_instance)
        layout.addWidget(self.access_button)

        # PID Label
        self.pid_label = QLabel("PID: Not Found")
        self.pid_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pid_label)

        self.setLayout(layout)

    def update_image(self):
        """Updates the displayed screenshot."""
        if self.snapshot_path.exists():
            pixmap = QPixmap(str(self.snapshot_path))
            if not pixmap.isNull():
                # Scale the pixmap to fit the label while keeping aspect ratio
                pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(pixmap)
            else:
                self.image_label.setText("Invalid Image")
                print(f"Invalid image at {self.snapshot_path}")
        else:
            self.image_label.setText("No Screenshot")
            print(f"Screenshot {self.snapshot_path} does not exist.")

    def is_pid_active(self, pid):
        """Checks if a given PID is active."""
        return psutil.pid_exists(pid)

    def retrieve_pid_if_needed(self):
        """Retrieves and stores the PID based on the window title if PID is not provided or inactive."""
        if self.pid and self.is_pid_active(self.pid):
            # PID is already provided and active
            self.pid_label.setText(f"PID: {self.pid}")
            print(f"Instance {self.instance_number} has active PID: {self.pid}")
        else:
            # Retrieve PID based on window title
            label = f"user{self.instance_number} - Chromium"
            retrieved_pid = get_pid_from_taskbar_label(label)
            if retrieved_pid and self.is_pid_active(retrieved_pid):
                self.pid = retrieved_pid
                self.pid_label.setText(f"PID: {self.pid}")
                print(f"Instance {self.instance_number} has PID: {self.pid}")
            else:
                self.pid = None
                self.pid_label.setText("PID: Not Found")
                print(f"No valid PID found for instance {self.instance_number} with label '{label}'")

    def access_instance(self):
        """Handles the Access button click by executing nircmd commands."""
        if self.pid and self.is_pid_active(self.pid):
            print(f"Attempting to execute nircmd commands on PID {self.pid} for instance {self.instance_number}")
            try:
                # Define the commands with '/' before the PID
                commands = [
                    ['nircmd', 'win', 'max', 'process', f'/{self.pid}'],
                    ['nircmd', 'win', 'min', 'process', f'/{self.pid}'],
                    ['nircmd', 'win', 'max', 'process', f'/{self.pid}'],
                ]

                for cmd in commands:
                    # Execute each command
                    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    print(f"Executed: {' '.join(cmd)}")
                    if result.stdout:
                        print(f"Output: {result.stdout}")
                    if result.stderr:
                        print(f"Error Output: {result.stderr}")

                success_message = f"Successfully executed nircmd commands on PID {self.pid}."
                print(success_message)
            except subprocess.CalledProcessError as e:
                error_message = f"Failed to execute command: {' '.join(e.cmd)}\nError: {e.stderr}"
                print(error_message)
                QMessageBox.critical(self, "Command Failed", error_message)
            except FileNotFoundError:
                error_message = "nircmd not found. Please ensure nircmd is installed and in your PATH."
                print(error_message)
                QMessageBox.critical(self, "nircmd Not Found", error_message)
            except Exception as e:
                error_message = f"An unexpected error occurred: {e}"
                print(error_message)
                QMessageBox.critical(self, "Error", error_message)
        else:
            error_message = f"No active PID available for instance {self.instance_number}. Cannot execute nircmd commands."
            print(error_message)
            QMessageBox.warning(self, "No PID", error_message)
            #very very clean huh

#handler for the gemini rebuilt browser automation scripts class/objects
class BrowserGUI(QWidget):
    def __init__(self, sessions_dir='sessions', screenshots_dir='screenshots', macros_dir='MACROS', max_columns=4):
        super().__init__()
        # Resolve absolute paths based on the script's directory
        script_dir = Path(__file__).parent.resolve()
        self.sessions_dir = (script_dir / sessions_dir).resolve()
        self.screenshots_dir = (script_dir / screenshots_dir).resolve()
        self.macros_dir = (script_dir / macros_dir).resolve()
        self.max_columns = max_columns
        self.instance_widgets = {}  # Maps instance_number to InstanceWidget
        self.init_ui()
        self.setup_file_watcher()

    def init_ui(self):
        self.setWindowTitle("Browser Instances Manager")
        self.setGeometry(100, 100, 900, 600)  # Width x Height

        main_layout = QVBoxLayout()

        # Top layout with Macro Selection and Refresh Button
        top_layout = QHBoxLayout()

        # Macro Dropdown
        self.macro_dropdown = QComboBox()
        self.macro_dropdown.setFixedWidth(300)
        self.macro_dropdown.addItem('NONE')  # Default option
        self.macro_dropdown.currentIndexChanged.connect(self.on_macro_selected)
        top_layout.addWidget(self.macro_dropdown, alignment=Qt.AlignLeft)

        # Refresh Button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setFixedWidth(150)
        self.refresh_button.clicked.connect(self.refresh_all)
        top_layout.addWidget(self.refresh_button, alignment=Qt.AlignRight)

        main_layout.addLayout(top_layout)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Container widget for grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)  # Increased spacing for better visuals
        self.grid_layout.setAlignment(Qt.AlignTop)
        self.grid_widget.setLayout(self.grid_layout)

        self.scroll_area.setWidget(self.grid_widget)
        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)

        # Load instances and macros initially
        self.refresh_all()

    def setup_file_watcher(self):
        """Sets up a QFileSystemWatcher to monitor the screenshots directory."""
        self.file_watcher = QFileSystemWatcher()
        if self.screenshots_dir.exists():
            self.file_watcher.addPath(str(self.screenshots_dir))
        self.file_watcher.directoryChanged.connect(self.on_screenshots_changed)

    def refresh_all(self):
        """Refresh all instances and macros."""
        self.load_instances()
        self.refresh_macros()

    def on_screenshots_changed(self, path):
        """Handles updates when screenshots are changed."""
        for instance_number, widget in self.instance_widgets.items():
            snapshot_path = self.screenshots_dir / f"user{instance_number}.png"
            widget.snapshot_path = snapshot_path
            widget.update_image()

    def load_instances(self):
        """Loads instances from instances.json and updates the grid."""
        instances_json = self.sessions_dir / 'instances.json'
        if not instances_json.exists():
            return
        try:
            with open(instances_json, 'r') as f:
                instances = json.load(f)
        except json.JSONDecodeError:
            return

        # Determine current instances
        current_instances = set(self.instance_widgets.keys())
        new_instances = set()

        for instance in instances:
            instance_number = instance.get('instance_number')
            if instance_number is None:
                continue
            new_instances.add(instance_number)
            snapshot_filename = f"user{instance_number}.png"
            snapshot_path = self.screenshots_dir / snapshot_filename

            if instance_number not in self.instance_widgets:
                # Create a new InstanceWidget
                instance_widget = InstanceWidget(instance_number, snapshot_path)
                self.instance_widgets[instance_number] = instance_widget

                # Add to grid
                total_instances = len(self.instance_widgets)
                row = (total_instances - 1) // self.max_columns
                col = (total_instances - 1) % self.max_columns
                self.grid_layout.addWidget(instance_widget, row, col)
            else:
                # Update existing widget's snapshot path
                widget = self.instance_widgets[instance_number]
                widget.snapshot_path = snapshot_path
                widget.update_image()

        # Remove widgets that are no longer active
        removed_instances = current_instances - new_instances
        for instance_number in removed_instances:
            widget = self.instance_widgets.pop(instance_number)
            self.grid_layout.removeWidget(widget)
            widget.setParent(None)

    def refresh_macros(self):
        """Refresh the macro dropdown."""
        if not self.macros_dir.exists():
            self.macros_dir.mkdir(parents=True)

        self.macro_dropdown.clear()
        self.macro_dropdown.addItem('NONE')  # Always include "NONE" option

        # Add only files from the MACROS directory
        macros = [f for f in self.macros_dir.iterdir() if f.is_file()]
        for macro in macros:
            self.macro_dropdown.addItem(macro.name)

    def on_macro_selected(self):
        """Handles macro selection dynamically."""
        selected_macro = self.macro_dropdown.currentText()
        macro_txt_path = Path.cwd() / "macro.txt"

        if selected_macro == 'NONE':
            # Remove macro.txt if NONE is selected
            if macro_txt_path.exists():
                macro_txt_path.unlink()
            print("Macro selection cleared.")
        else:
            selected_macro_path = self.macros_dir / selected_macro
            if selected_macro_path.exists() and selected_macro_path.is_file():
                try:
                    if macro_txt_path.exists():
                        macro_txt_path.unlink()
                    shutil.copy(selected_macro_path, macro_txt_path)
                    print(f"Macro '{selected_macro}' set as active.")
                except PermissionError as e:
                    QMessageBox.critical(self, "Permission Error", f"Unable to copy macro file.\n{e}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{e}")
            else:
                print(f"Selected macro '{selected_macro}' does not exist or is not a file.")

    def closeEvent(self, event):
        """Handles the window close event."""
        reply = QMessageBox.question(
            self,
            'Quit',
            'Are you sure you want to quit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    gui = BrowserGUI()
    gui.show()
    sys.exit(app.exec_())

#simple GUI REMOVED (RENAMING, SOCKS5 PARSING/CONFIG, Single macro support selection dropdown, & launch silently in on hidden screen) 
#for obv reasons but renaming was built into that custom watcher function so it got remvoed in the proccess :) - (RENDITION BEFORE REMOVAL 552 lines) MOSTLY WHITESPACE cause gemini makes my code clean XD
if __name__ == "__main__":
    main()
