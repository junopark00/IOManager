# -*- coding: utf-8 -*-

import PyOpenColorIO as OCIO
from PySide2.QtCore import Qt
from PySide2.QtWidgets import ( QSizePolicy, QMenu, QToolButton,
                               QAction, QApplication)


class CustomComboBox(QToolButton):
    def __init__(self, ocio_path):
        super(CustomComboBox, self).__init__()
        
        self.colorspace_names = []
        
        self.set_widgets()
        self.__load_ocio(ocio_path)
        
    def reload_path(self, ocio_path):
        self.__load_ocio(ocio_path)

    def set_widgets(self):
        # set combo_button size always maximum
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setLayoutDirection(Qt.LeftToRight)
        self.setText("Select Colorspace")

        self.menu = QMenu(self)
        self.input_menu = None
        
    def __load_ocio(self, ocio_path):
        # clear the menu
        self.menu.clear()
        
        aces_list, input_list, output_list, utility_list, etc_list = self.separate_colorspaces(ocio_path)
        for name in aces_list:
            self.add_sub_menu("ACES", name)
        for name in input_list:
            self.add_input_menu(name)
        for name in output_list:
            self.add_sub_menu("Output", name)
        for name in utility_list:
            self.add_sub_menu("Utility", name)
        for name in etc_list:
            self.add_sub_menu("Aliases", name)

        self.setMenu(self.menu)
        self.setPopupMode(QToolButton.InstantPopup)
        
    @property
    def combo_text(self):
        return self.text()
    
    @property
    def color_list(self):
        return self.colorspace_names
    
    def set_combo_text(self, text):
        self.setText(text)
        
    def separate_colorspaces(self, ocio_path):
        config = OCIO.Config.CreateFromFile(ocio_path)

        colorspaces = config.getColorSpaces()
        self.colorspace_names = [cs.getName() for cs in colorspaces]

        aces_list = []
        input_list = []
        output_list = []
        utility_list = []
        etc_list = []
        
        for name in self.colorspace_names:
            if name.startswith("ACES"):
                aces_list.append(name)
            elif name.startswith("Input"):
                input_list.append(name)
            elif name.startswith("Output") or name.startswith("Client"):
                output_list.append(name)
            elif name.startswith("Utility") or name.startswith("Role"):
                utility_list.append(name)
            else:
                etc_list.append(name)
        
        return aces_list, input_list, output_list, utility_list, etc_list
        
    def add_menu(self, text):
        """
        Add a single Menu item to the QMenu

        Args:
            text (str): The text to display on the menu item
        """
        action = QAction(text, self)
        action.triggered.connect(lambda: self.on_action_clicked(text))
        self.menu.addAction(action)
        
    def add_sub_menu(self, text, sub_text):
        """
        Find the menu item and add a sub menu item

        Args:
            text (str): The text to display on the menu item
            sub_text (str): The text to display on the sub menu item
        """
        sub_action = QAction(sub_text, self)
        sub_action.triggered.connect(lambda: self.on_action_clicked(sub_text))
        for action in self.menu.actions():
            if action.text() == text:
                action.menu().addAction(sub_action)
                return
        menu = self.menu.addMenu(text)
        menu.addAction(sub_action)
        
    def add_input_menu(self, text):
        """
        If Input Colorspace, separate details like Input - Adx, Input - AlexaV3LogC, etc.
        and further separate by camera manufacturer.

        Args:
            text (str): The text to display on the menu item
        """
        manufacturer = text.split(" - ")[1]

        # Find or create the 'Input' menu
        if self.input_menu is None:
            self.input_menu = self.menu.addMenu("Input")
            
        # Find or create the manufacturer menu
        manufacturer_menu = None
        for action in self.input_menu.actions():
            if action.text() == manufacturer:
                manufacturer_menu = action.menu()
                break
        if manufacturer_menu is None:
            manufacturer_menu = self.input_menu.addMenu(manufacturer)
            
        sub_action = QAction(text, self)
        sub_action.triggered.connect(lambda: self.on_action_clicked(text))
        manufacturer_menu.addAction(sub_action)
            
    def on_action_clicked(self, text):
        self.setText(text)
        
        
if __name__ == "__main__":
    test_path = r"V:\ORV\stuff\spec\_OCIO\config.ocio"
    app = QApplication([])
    window = CustomComboBox(test_path)
    window.show()
    app.exec_()