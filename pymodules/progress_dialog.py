# -*- coding: utf-8 -*-

import sys
from PySide2.QtWidgets import ( QWidget, QLabel, QProgressBar,
                               QVBoxLayout, QApplication )
from PySide2.QtCore import Qt

class ProgressDialog(QWidget):
    def __init__(self, msg, range_end, parent=None):
        super(ProgressDialog, self).__init__(parent)
        
        self.msg = msg
        self.range_end = range_end
        self.parent = parent
        self.setWindowTitle("Generating")
        self.setFixedSize(240, 150)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.ApplicationModal)
        
        self.set_widgets()
        self.set_layout()
        self.set_stylesheet()
        
    def set_widgets(self):
        self.label_text = QLabel(self.msg, self)
        self.label_text.setAlignment(Qt.AlignCenter)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, self.range_end)
        self.progress_bar.setValue(0)
        
    def set_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(self.label_text)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        
    def set_stylesheet(self):
        self.setStyleSheet("""
            QLabel {
                color: rgb(138, 180, 247);
                font-family: Lato;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
    def center_on_parent(self, parent):
        screen = QApplication.screenAt(parent.geometry().center())
        if screen:
            parent_center = parent.geometry().center()
            self.move(parent_center.x() - self.width() // 2, parent_center.y() - self.height() // 2)
                
    def show(self):
        if self.parent:
            # Center the dialog on the parent widget
            self.center_on_parent(self.parent)
        super(ProgressDialog, self).show()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = ProgressDialog("")
    dialog.show()
    sys.exit(app.exec_())