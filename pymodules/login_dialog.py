# -*- coding: utf-8 -*-

import os
import sys

import qdarktheme
from PySide2.QtWidgets import ( QDialog, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QHBoxLayout, QApplication )
from PySide2.QtGui import QIcon, QFontDatabase, QFont
from PySide2.QtCore import Qt, QSettings

# Custom Modules
import sg_manager
import constants
from init_logger import IOManagerLogger

# Set Logger
logger = IOManagerLogger(os.path.basename(__file__), constants.LOG_PATH)


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        
        self.setWindowTitle("IO-Manager: ShotGrid Login")
        self.setWindowIcon(QIcon("./resources/Icon/main.png"))
        self.setFixedSize(380, 90)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)
        
        self.parent = parent
        self.login_success = False
        
        already_login, self.user_data = self.get_settings()
        if already_login:
            self.login_success = True
            return
        
        self.set_widgets()
        self.set_layout()
        self.set_font()
        self.connections()
        qdarktheme.setup_theme()
        
    def get_settings(self):
        settings = QSettings("MTHD", "IOManager")
        email = settings.value("user_email")
        
        if not email:
            return False, None
        
        user_data = sg_manager.get_user_by_email(email)
        
        if not user_data:
            return False, None
        
        return True, user_data
    
    def set_widgets(self):
        self.label_email = QLabel("Email", self)
        self.lineedit_email = QLineEdit(self)
        self.lineedit_email.setPlaceholderText("ex) username@mortarheadd.co.kr")
        self.button_login = QPushButton("Login", self)
        self.button_login.setFixedWidth(60)
    
    def set_layout(self):
        layout = QHBoxLayout()
        layout.addWidget(self.label_email)
        layout.addWidget(self.lineedit_email)
        layout.addWidget(self.button_login)
        self.setLayout(layout)
        
    def set_font(self):
        font_path = "./resources/font/Lato-Bold.ttf"
        if not os.path.exists(font_path):
            print("Font file not found")
            pass
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("Font file not loaded")
            pass
        else:
            font = QFontDatabase.applicationFontFamilies(font_id)[0]
            QApplication.setFont(QFont(font, 10))
            
    def connections(self):
        self.button_login.clicked.connect(self.login)
        self.lineedit_email.returnPressed.connect(self.login)
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter:
            self.login()
            
    def login(self):
        email = self.lineedit_email.text()
        try:
            self.user_data = sg_manager.get_user_by_email(email)
            
            if not self.user_data:
                QMessageBox.critical(self, "ShotGrid Login Error", "ShotGrid에 로그인할 수 없습니다.")
                return
            
            self.login_success = True
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "ShotGrid Login Error", "ShotGrid에 로그인할 수 없습니다.")
            self.user_data = None
            
    def exec_(self):
        if self.login_success:
            return self.login_success, self.user_data
        
        super(LoginDialog, self).exec_()
        return self.login_success, self.user_data
    
    def closeEvent(self, event):
        # When this dialog is closed, the application should be closed
        try:
            self.parent.close()
        finally:
            sys.exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = LoginDialog()
    if dialog.login_success:
        sys.exit(0)
    else:
        dialog.show()
        sys.exit(app.exec_())