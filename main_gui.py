"""Password Manager — GUI version built with PyQt6."""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import VERSION, KEY_FILE
from app.crypto.key_manager import load_or_create_key
from app.crypto.encryption import init_fernet
from app.database.connection import init_db
from app.database.repository import Repository
from app.services.password_service import PasswordService
from app.services.password_generator import generate_password
from app.utils.password_strength import check_password_strength_gui

# ── Initialised in main() ────────────────────────────────────────────────

service: PasswordService

# ── Stylesheet ───────────────────────────────────────────────────────────

STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
}

QWidget {
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QLabel {
    color: #cdd6f4;
    font-size: 14px;
}

QLineEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    color: #cdd6f4;
    selection-background-color: #585b70;
}

QLineEdit:focus {
    border: 1px solid #89b4fa;
}

QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #74c7ec;
}

QPushButton:pressed {
    background-color: #89dceb;
}

QPushButton#sidebarBtn {
    background-color: transparent;
    color: #cdd6f4;
    text-align: left;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: normal;
}

QPushButton#sidebarBtn:hover {
    background-color: #313244;
}

QPushButton#sidebarBtn:checked {
    background-color: #45475a;
    color: #89b4fa;
}

QPushButton#dangerBtn {
    background-color: #f38ba8;
}

QPushButton#dangerBtn:hover {
    background-color: #eba0ac;
}

QPushButton#secondaryBtn {
    background-color: #45475a;
    color: #cdd6f4;
}

QPushButton#secondaryBtn:hover {
    background-color: #585b70;
}

QTableWidget {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 8px;
    gridline-color: #45475a;
    font-size: 13px;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #45475a;
    color: #89b4fa;
}

QHeaderView::section {
    background-color: #1e1e2e;
    color: #89b4fa;
    border: none;
    border-bottom: 2px solid #45475a;
    padding: 10px;
    font-weight: bold;
    font-size: 13px;
}

QFrame#sidebar {
    background-color: #181825;
    border-right: 1px solid #313244;
}

QFrame#centralWidget {
    background-color: #1e1e2e;
}

QSpinBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px;
    font-size: 14px;
    color: #cdd6f4;
}

QSpinBox:focus {
    border: 1px solid #89b4fa;
}

QSpinBox::up-button, QSpinBox::down-button {
    background-color: #45475a;
    border: none;
    width: 20px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #585b70;
}

QStatusBar {
    background-color: #181825;
    color: #6c7086;
    border-top: 1px solid #313244;
}

QCheckBox {
    color: #cdd6f4;
    font-size: 14px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #45475a;
    background-color: #313244;
}

QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}

QMessageBox {
    background-color: #1e1e2e;
}

QDialog {
    background-color: #1e1e2e;
}

QLabel#titleLabel {
    font-size: 24px;
    font-weight: bold;
    color: #89b4fa;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #6c7086;
}

QLabel#sectionLabel {
    font-size: 16px;
    font-weight: bold;
    color: #cba6f7;
}

QLabel#strengthWeak {
    color: #f38ba8;
    font-weight: bold;
}

QLabel#strengthMedium {
    color: #f9e2af;
    font-weight: bold;
}

QLabel#strengthStrong {
    color: #a6e3a1;
    font-weight: bold;
}

QLabel#strengthVeryStrong {
    color: #94e2d5;
    font-weight: bold;
}

QLabel#generatedPassword {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 12px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 16px;
    color: #a6e3a1;
    selection-background-color: #585b70;
}

QLabel#infoLabel {
    font-size: 12px;
    color: #6c7086;
}
"""


# ── Sidebar Button ───────────────────────────────────────────────────────


class SidebarButton(QPushButton):
    """A checkable sidebar navigation button with custom styling."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("sidebarBtn")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(45)


# ── Add Password Widget ─────────────────────────────────────────────────


class AddPasswordWidget(QWidget):
    """Widget for adding a new credential."""

    def __init__(self, svc: PasswordService, status_callback=None, parent=None):
        super().__init__(parent)
        self.service = svc
        self.status_callback = status_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 30)

        title = QLabel("Add New Password")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Store a new credential securely")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        form_layout = QFormLayout()
        form_layout.setSpacing(16)

        self.site_input = QLineEdit()
        self.site_input.setPlaceholderText("e.g., github.com")
        form_layout.addRow("Site:", self.site_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g., john@example.com")
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.textChanged.connect(self.update_strength)
        form_layout.addRow("Password:", self.password_input)

        self.show_password_cb = QCheckBox("Show password")
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        form_layout.addRow("", self.show_password_cb)

        layout.addLayout(form_layout)

        self.strength_label = QLabel("")
        self.strength_label.setObjectName("infoLabel")
        layout.addWidget(self.strength_label)

        layout.addSpacing(10)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        save_btn = QPushButton("Save Password")
        save_btn.clicked.connect(self.save_password)
        btn_layout.addWidget(save_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.clicked.connect(self.clear_form)
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def toggle_password_visibility(self, checked: bool):
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def update_strength(self, text: str):
        if not text:
            self.strength_label.setText("")
            self.strength_label.setObjectName("infoLabel")
            return
        label, color, style_id = check_password_strength_gui(text)
        self.strength_label.setText(f"Strength: {label}")
        self.strength_label.setObjectName(style_id)
        self.strength_label.style().unpolish(self.strength_label)
        self.strength_label.style().polish(self.strength_label)

    def save_password(self):
        site = self.site_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not site or not username or not password:
            QMessageBox.warning(self, "Validation Error",
                                "All fields are required.")
            return

        self.service.add(site, username, password)

        self.clear_form()
        if self.status_callback:
            self.status_callback("Password saved successfully")

    def clear_form(self):
        self.site_input.clear()
        self.username_input.clear()
        self.password_input.clear()
        self.strength_label.setText("")


# ── Password List Widget ─────────────────────────────────────────────────


class PasswordListWidget(QWidget):
    """Widget for viewing, editing, and deleting stored credentials."""

    def __init__(self, svc: PasswordService, status_callback=None, parent=None):
        super().__init__(parent)
        self.service = svc
        self.status_callback = status_callback
        self.setup_ui()
        self.load_passwords()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 30)

        header_layout = QHBoxLayout()

        title = QLabel("Password Vault")
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)

        header_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.clicked.connect(self.load_passwords)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        subtitle = QLabel("All stored credentials")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Site", "Username", "Created"])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setColumnWidth(0, 60)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        view_btn = QPushButton("View Password")
        view_btn.setObjectName("secondaryBtn")
        view_btn.clicked.connect(self.view_password)
        btn_layout.addWidget(view_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_password)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("dangerBtn")
        delete_btn.clicked.connect(self.delete_password)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        layout.addLayout(btn_layout)

    def load_passwords(self):
        rows = self.service.list_all()

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.table.setItem(i, 2, QTableWidgetItem(row[2]))
            self.table.setItem(i, 3, QTableWidgetItem(row[3]))

        if self.status_callback:
            self.status_callback(f"Loaded {len(rows)} password(s)")

    def get_selected_id(self) -> int | None:
        selected = self.table.currentRow()
        if selected < 0:
            return None
        id_item = self.table.item(selected, 0)
        return int(id_item.text()) if id_item else None

    def view_password(self):
        entry_id = self.get_selected_id()
        if entry_id is None:
            QMessageBox.information(self, "No Selection",
                                    "Please select a password to view.")
            return

        details = self.service.get_details(entry_id)
        if details:
            site, username, decrypted = details
            QMessageBox.information(
                self, "Password Details",
                f"Site: {site}\nUsername: {username}\nPassword: {decrypted}"
            )

    def edit_password(self):
        entry_id = self.get_selected_id()
        if entry_id is None:
            QMessageBox.information(self, "No Selection",
                                    "Please select a password to edit.")
            return

        details = self.service.get_details(entry_id)
        if details:
            site, username, decrypted = details
            dialog = EditPasswordDialog(
                entry_id, site, username, decrypted, self.service, self
            )
            if dialog.exec():
                self.load_passwords()
                if self.status_callback:
                    self.status_callback("Password updated successfully")

    def delete_password(self):
        entry_id = self.get_selected_id()
        if entry_id is None:
            QMessageBox.information(self, "No Selection",
                                    "Please select a password to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this password?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.service.delete(entry_id)
            self.load_passwords()
            if self.status_callback:
                self.status_callback("Password deleted")


# ── Edit Password Dialog ─────────────────────────────────────────────────


class EditPasswordDialog(QDialog):
    """Dialog for editing an existing credential."""

    def __init__(self, entry_id: int, site: str, username: str,
                 password: str, svc: PasswordService, parent=None):
        super().__init__(parent)
        self.entry_id = entry_id
        self.service = svc
        self.setWindowTitle("Edit Password")
        self.setMinimumWidth(400)
        self.setup_ui(site, username, password)

    def setup_ui(self, site: str, username: str, password: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.site_input = QLineEdit(site)
        form_layout.addRow("Site:", self.site_input)

        self.username_input = QLineEdit(username)
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit(password)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)

        self.show_password_cb = QCheckBox("Show password")
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        form_layout.addRow("", self.show_password_cb)

        layout.addLayout(form_layout)

        self.strength_label = QLabel("")
        self.strength_label.setObjectName("infoLabel")
        layout.addWidget(self.strength_label)

        self.password_input.textChanged.connect(self.update_strength)
        self.update_strength(password)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def toggle_password_visibility(self, checked: bool):
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def update_strength(self, text: str):
        if not text:
            self.strength_label.setText("")
            self.strength_label.setObjectName("infoLabel")
            return
        label, color, style_id = check_password_strength_gui(text)
        self.strength_label.setText(f"Strength: {label}")
        self.strength_label.setObjectName(style_id)
        self.strength_label.style().unpolish(self.strength_label)
        self.strength_label.style().polish(self.strength_label)

    def save_changes(self):
        site = self.site_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not site or not username or not password:
            QMessageBox.warning(self, "Validation Error",
                                "All fields are required.")
            return

        self.service.update(self.entry_id, site, username, password)
        self.accept()


# ── Password Generator Widget ───────────────────────────────────────────


class PasswordGeneratorWidget(QWidget):
    """Widget for generating cryptographically secure passwords."""

    def __init__(self, status_callback=None, parent=None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 30)

        title = QLabel("Password Generator")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Generate a secure random password")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        length_layout = QHBoxLayout()
        length_layout.setSpacing(12)

        length_label = QLabel("Password Length:")
        length_layout.addWidget(length_label)

        self.length_spin = QSpinBox()
        self.length_spin.setRange(4, 128)
        self.length_spin.setValue(16)
        self.length_spin.setFixedWidth(100)
        length_layout.addWidget(self.length_spin)

        length_layout.addStretch()
        layout.addLayout(length_layout)

        layout.addSpacing(10)

        generated_label = QLabel("Generated Password:")
        generated_label.setObjectName("sectionLabel")
        layout.addWidget(generated_label)

        self.password_display = QLabel("Click 'Generate' to create a password")
        self.password_display.setObjectName("generatedPassword")
        self.password_display.setWordWrap(True)
        self.password_display.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.password_display)

        self.strength_label = QLabel("")
        self.strength_label.setObjectName("infoLabel")
        layout.addWidget(self.strength_label)

        layout.addSpacing(20)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        generate_btn = QPushButton("Generate")
        generate_btn.clicked.connect(self.generate_password)
        btn_layout.addWidget(generate_btn)

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.setObjectName("secondaryBtn")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_layout.addWidget(copy_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def generate_password(self):
        length = self.length_spin.value()
        password = generate_password(length)
        self.password_display.setText(password)

        label, color, style_id = check_password_strength_gui(password)
        self.strength_label.setText(f"Strength: {label}")
        self.strength_label.setObjectName(style_id)
        self.strength_label.style().unpolish(self.strength_label)
        self.strength_label.style().polish(self.strength_label)

        if self.status_callback:
            self.status_callback("Password generated")

    def copy_to_clipboard(self):
        password = self.password_display.text()
        if password and password != "Click 'Generate' to create a password":
            clipboard = QApplication.clipboard()
            clipboard.setText(password)
            if self.status_callback:
                self.status_callback("Password copied to clipboard")


# ── Main Window ──────────────────────────────────────────────────────────


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""

    def __init__(self, svc: PasswordService):
        super().__init__()
        self.service = svc
        self.setWindowTitle(f"Password Manager v{VERSION}")
        self.setMinimumSize(900, 600)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(4)

        app_label = QLabel("🔑 Password\nManager")
        app_label.setObjectName("subtitleLabel")
        app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #89b4fa;")
        sidebar_layout.addWidget(app_label)

        sidebar_layout.addSpacing(20)

        self.nav_buttons = []

        btn_add = SidebarButton("  ➕  Add Password")
        btn_add.clicked.connect(lambda: self.switch_page(0))
        sidebar_layout.addWidget(btn_add)
        self.nav_buttons.append(btn_add)

        btn_list = SidebarButton("  📋  Password List")
        btn_list.clicked.connect(lambda: self.switch_page(1))
        sidebar_layout.addWidget(btn_list)
        self.nav_buttons.append(btn_list)

        btn_generator = SidebarButton("  🔐  Generator")
        btn_generator.clicked.connect(lambda: self.switch_page(2))
        sidebar_layout.addWidget(btn_generator)
        self.nav_buttons.append(btn_generator)

        sidebar_layout.addStretch()

        version_label = QLabel(f"v{VERSION}")
        version_label.setObjectName("subtitleLabel")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(version_label)

        main_layout.addWidget(sidebar)

        self.stack = QStackedWidget()

        self.add_widget = AddPasswordWidget(
            self.service, status_callback=self.show_status, parent=self
        )
        self.list_widget = PasswordListWidget(
            self.service, status_callback=self.show_status, parent=self
        )
        self.generator_widget = PasswordGeneratorWidget(
            status_callback=self.show_status, parent=self
        )

        self.stack.addWidget(self.add_widget)
        self.stack.addWidget(self.list_widget)
        self.stack.addWidget(self.generator_widget)

        main_layout.addWidget(self.stack)

        self.statusBar().showMessage("Ready")
        self.switch_page(0)

    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        if index == 1:
            self.list_widget.load_passwords()

    def show_status(self, message: str):
        self.statusBar().showMessage(message, 5000)


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    global service
    key = load_or_create_key()
    init_fernet(key)
    init_db()

    repo = Repository()
    service = PasswordService(repo)

    window = MainWindow(service)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
