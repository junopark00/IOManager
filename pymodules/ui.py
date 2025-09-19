# -*- coding: utf-8 -*-

import os
import sys

py37_module_path = r"W:\MTHD_core\GlobalLib\Python37"
if py37_module_path not in sys.path:
    sys.path.append(py37_module_path)
    
import qdarktheme
from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QIcon, QFontDatabase, QFont
from PySide2.QtWidgets import ( QMainWindow, QTabWidget, QWidget, QLabel, QComboBox, QLineEdit,
                               QPushButton, QSizePolicy, QFrame, QSpacerItem, QToolButton, QTableWidget,
                               QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox, QGridLayout, QHBoxLayout,
                               QVBoxLayout, QSplitter, QApplication, QMenuBar, QStatusBar )

# Load Custom Modules
import pymodules.constants as constants
from pymodules import aces_combobox


class IOManager_UI(QMainWindow):
    def __init__(self):
        super(IOManager_UI, self).__init__()
        # self.setup_ui()
        
    def setup_ui(self):
        self.__set_widgets()
        self.__set_layout()
        self.__set_stylesheet()
        self.__set_font()
        self.__set_menu_bar()
        self.__set_status_bar()
        qdarktheme.setup_theme()
        
    def __set_widgets(self):
        self.setWindowTitle("IO Manager")
        self.resource_path = "W:/MTHD_core/standalone/io-manager/resources"
        self.setWindowIcon(QIcon(os.path.join(self.resource_path, "Icon", "main.png")))
        self.setMinimumSize(1600, 900)
        # Tab widget
        self.tab_widget = QTabWidget()
        
        self.__set_tab_1() # Plate Tab
        self.__set_tab_2() # Edit Tab
        
    def __set_tab_1(self):
        """
        Plate Tab
        """
        # Tab 1
        self.tab_plate = QWidget()
        self.tab_widget.addTab(self.tab_plate, "Plate")
        
        ## Set Project
        self.project_lb = QLabel("Project")
        self.project_cmbx = QComboBox()
        self.project_cmbx.setFixedSize(200, 30)
        
        ## Browse Scan Folder
        self.scan_folder_lb = QLabel("Scan Folder")
        self.scan_folder_le = QLineEdit()
        # self.scan_folder_le.setReadOnly(True)
        self.scan_folder_btn = QPushButton("Open")
        self.scan_folder_btn.setFixedWidth(80)
        
        ## Excel File
        self.excel_file_lb = QLabel("Excel File")
        self.excel_file_cmbx = QComboBox()
        self.excel_file_cmbx.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.excel_file_create_btn = QPushButton("Create New Excel")
        
        self.excel_file_load_btn = QPushButton("Load")
        self.excel_file_load_btn.setFixedWidth(80)
        self.excel_file_load_btn.setDisabled(True)
        
        ## Tools
        self.h_divider = QFrame()
        self.h_divider.setFrameShape(QFrame.HLine)
        self.h_divider.setFrameShadow(QFrame.Sunken)
        
        self.scan_folder_open_btn = QPushButton("Open Scan Folder")
        self.excel_file_open_btn = QPushButton("Open Excel File")
        
        self.h_expander = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.scan_folder_reload_btn = QToolButton()
        self.scan_folder_reload_btn.setFixedSize(30, 30)
        self.scan_folder_reload_btn.setIcon(QIcon(os.path.join(self.resource_path, "Icon", "reload_white.png")))
        self.scan_folder_reload_btn.setToolTip("Reload Scan Folder")
        
        self.view_mode_btn = QToolButton()
        self.show_icon = QIcon(os.path.join(self.resource_path, "Icon", "eye_show_white.png"))
        self.hide_icon = QIcon(os.path.join(self.resource_path, "Icon", "eye_hide_white.png"))
        self.view_mode_btn.setIcon(self.show_icon)
        self.view_mode_btn.setIconSize(QSize(25, 25))
        self.view_mode_btn.setFixedSize(30, 30)
        self.view_mode_btn.setToolTip("View Mode")
        
        ## Table Widget
        self.plate_table_widget = QTableWidget()
        self.table_headers = constants.HEADERS
        
        ### Set table widget
        self.plate_table_widget.setSortingEnabled(True)
        self.plate_table_widget.setColumnCount(len(self.table_headers))
        self.plate_table_widget.setHorizontalHeaderLabels(self.table_headers)
        self.plate_table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        h_header = self.plate_table_widget.horizontalHeader()
        v_header = self.plate_table_widget.verticalHeader()
        h_header.setCascadingSectionResizes(False)
        h_header.setDefaultSectionSize(100)
        h_header.setStretchLastSection(True)
        v_header.setDefaultSectionSize(30)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("Render"), 60)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("Thumbnail"), 200)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("Scan Data"), 200)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("Clip Name"), 230)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("Version Description"), 180)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("Cube"), 150)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("TimeCode In"), 120)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("TimeCode Out"), 120)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("First Frame Offset"), 140)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("End Frame Offset"), 140)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("Retime End Frame"), 140)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("Retime TimeCode Out"), 150)
        self.plate_table_widget.setColumnWidth(self.table_headers.index("Retime Speed"), 110)
        
        # Render Settings
        ## Export Option
        self.render_export_lb = QLabel("Export To")
        self.render_export_exr = QCheckBox("EXR")
        self.render_export_exr.setChecked(True)
        self.render_export_mov = QCheckBox("MOV")
        self.render_export_mov.setChecked(True)
        self.render_export_jpg = QCheckBox("JPG")
        self.render_export_jpg.setChecked(True)
        self.render_export_png = QCheckBox("PNG")
        self.render_export_png.setChecked(False)
        
        # Resize Settings
        ### Resize - Resize Target
        self.resize_target_lb = QLabel("Resize Target")
        self.resize_target_all_cb = QCheckBox("All")
        self.resize_target_mov_cb = QCheckBox("MOV Only")
        self.resize_target_all_cb.setChecked(True)
        self.resize_target_mov_cb.setChecked(False)
        
        ### Resize - Reformat
        self.render_reformat_lb = QLabel("Reformat")
        self.render_reformat_x_spbx = QSpinBox()
        self.render_reformat_x_spbx.setRange(0, 9999)
        self.render_reformat_x_spbx.setFixedWidth(100)
        self.render_reformat_x_spbx.setEnabled(False)
        self.render_reformat_x_lb = QLabel("X")
        self.render_reformat_y_spbx = QSpinBox()
        self.render_reformat_y_spbx.setRange(0, 9999)
        self.render_reformat_y_spbx.setFixedWidth(100)
        self.render_reformat_y_spbx.setEnabled(False)
        self.render_reformat_cmbx = QComboBox()
        reformat_list = constants.REFORMAT_PRESETS
        self.render_reformat_cmbx.addItems(reformat_list)
        
        ### Resize - Aspect Correction
        self.render_aspect_correction_lb = QLabel("Aspect Fit Mode")
        self.render_aspect_fit_cmbx = QComboBox()
        aspect_fit_modes = [
            "Extend Top/Bottom", # 세로 연장 (슬레이트)
            "Crop Left/Right"   # 양 옆 잘라서 맞춤
        ]
        self.render_aspect_fit_cmbx.addItems(aspect_fit_modes)
        # self.render_aspect_fit_cmbx.setFixedWidth(120)
        
        ### Resize - Crop
        self.render_crop_lb = QLabel("Crop")
        self.render_crop_x_spbx = QSpinBox()
        self.render_crop_x_spbx.setRange(0, 9999)
        self.render_crop_x_spbx.setFixedWidth(100)
        self.render_crop_x_spbx.setEnabled(False)
        self.render_crop_x_lb = QLabel("X")
        self.render_crop_y_spbx = QSpinBox()
        self.render_crop_y_spbx.setRange(0, 9999)
        self.render_crop_y_spbx.setFixedWidth(100)
        self.render_crop_y_spbx.setEnabled(False)
        
        self.render_crop_cmbx = QComboBox()
        crop_list = constants.CROP_PRESETS
        self.render_crop_cmbx.addItems(crop_list)
        
        ## FPS
        self.render_fps_lb = QLabel("FPS")
        self.render_fps_cmbx = QComboBox()
        fps_list = constants.FPS_PRESETS
        self.render_fps_cmbx.addItems(fps_list)
        self.render_fps_spbx = QDoubleSpinBox()
        self.render_fps_spbx.setRange(0.0, 999.0)
        self.render_fps_spbx.setSingleStep(0.1)
        self.render_fps_spbx.setDecimals(3)
        
        ## Codec
        self.render_codec_lb = QLabel("Codec")
        self.render_codec_cmbx = QComboBox()
        codec_list = constants.CODECS
        self.render_codec_cmbx.addItems(codec_list)
        
        ## Start Frame
        self.render_start_frame_lb = QLabel("Start Frame")
        self.render_start_frame_spbx = QSpinBox()
        self.render_start_frame_spbx.setRange(0, 10000)
        self.render_start_frame_spbx.setValue(1001)
        
        ## Priority
        self.render_priority_lb = QLabel("Priority")
        self.render_priority_spbx = QSpinBox()
        self.render_priority_spbx.setRange(1, 100)
        self.render_priority_spbx.setValue(50)
        
        # Colorspace
        ## Switch Colorspace
        self.colorspace_switch_lb = QLabel("Switch Colorspace")
        self.colorspace_switch_btn = QPushButton("Use Nuke Default")
        
        ## Path to OCIO Config
        self.colorspace_ocio_lb = QLabel("OCIO Config")
        self.colorspace_ocio_le = QLineEdit(constants.DEFAULT_OCIO_CONFIG)
        self.colorspace_ocio_btn = QPushButton("...")
        self.colorspace_ocio_btn.setFixedWidth(40)
        
        ## Input Colorspace
        self.colorspace_input_lb = QLabel("Input Colorspace")
        self.colorspace_input_cmbx = aces_combobox.CustomComboBox(self.colorspace_ocio_le.text())
        self.colorspace_input_cmbx_nuke = QComboBox()
        self.colorspace_input_cmbx_nuke.addItems(constants.NUKE_DEFAULT_COLORSPACES)
        self.colorspace_input_cmbx_nuke.hide()
        
        ## Output Colorspace
        self.colorspace_output_lb = QLabel("Output Colorspace")
        self.colorspace_output_cmbx = aces_combobox.CustomComboBox(self.colorspace_ocio_le.text())
        self.colorspace_output_cmbx_nuke = QComboBox()
        self.colorspace_output_cmbx_nuke.addItems(constants.NUKE_DEFAULT_COLORSPACES)
        self.colorspace_output_cmbx_nuke.hide()
        
        ## LUT
        self.colorspace_cube_lb = QLabel("Cube Folder")
        self.colorspace_cube_le = QLineEdit()
        self.colorspace_cube_btn = QPushButton("...")
        self.colorspace_cube_btn.setFixedWidth(40)
        
        # Buttons
        self.v_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.validate_btn = QPushButton("Validate Version")
        self.validate_btn.setFixedWidth(120)
        self.h_spacer = QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.collect_btn = QPushButton("Collect")
        self.collect_btn.setFixedWidth(80)
        self.render_btn = QPushButton("Render")
        self.render_btn.setFixedWidth(80)
        
        # Set All Labels Fixed Size
        self.render_export_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.render_reformat_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.render_reformat_x_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.render_aspect_correction_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))        
        self.render_crop_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.render_crop_x_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.render_fps_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.render_codec_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.render_start_frame_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.render_priority_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.colorspace_ocio_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.colorspace_input_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.colorspace_output_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.colorspace_cube_lb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        
    def __set_tab_2(self):
        """
        Edit Tab
        """
        # Tab 2
        self.tab_edit = QWidget()
        self.temp_widget = QWidget()
        self.tab_widget.addTab(self.tab_edit, "Edit")
        
        ## Set Project
        self.edit_project_lb = QLabel("Project")
        self.edit_project_cmbx = QComboBox()
        self.edit_project_cmbx.setFixedSize(200, 30)
        
        ## Browse Scan Folder
        self.edit_scan_folder_lb = QLabel("Scan Folder")
        self.edit_scan_folder_le = QLineEdit()
        # self.edit_scan_folder_le.setReadOnly(True)
        self.edit_scan_folder_btn = QPushButton("Open")
        self.edit_scan_folder_btn.setFixedWidth(80)
        
        ## Excel File
        self.edit_excel_file_lb = QLabel("Excel File")
        self.edit_excel_file_cmbx = QComboBox()
        self.edit_excel_file_cmbx.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))
        self.edit_excel_file_create_btn = QPushButton("Create New Excel")
        
        self.edit_task_cmbx = QComboBox()
        self.edit_task_cmbx.addItems(["edit", "editPost"])
        
        self.edit_excel_file_load_btn = QPushButton("Load")
        self.edit_excel_file_load_btn.setFixedWidth(80)
        self.edit_excel_file_load_btn.setDisabled(True)
        
        ## Tools
        self.edit_h_divider = QFrame()
        self.edit_h_divider.setFrameShape(QFrame.HLine)
        self.edit_h_divider.setFrameShadow(QFrame.Sunken)
        
        self.edit_scan_folder_open_btn = QPushButton("Open Scan Folder")
        self.edit_excel_file_open_btn = QPushButton("Open Excel File")
        
        self.edit_h_expander = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.edit_scan_folder_reload_btn = QToolButton()
        self.edit_scan_folder_reload_btn.setFixedSize(30, 30)
        self.edit_scan_folder_reload_btn.setIcon(QIcon(os.path.join(self.resource_path, "Icon", "reload_white.png")))
        self.edit_scan_folder_reload_btn.setToolTip("Reload Scan Folder")
        
        self.edit_view_mode_btn = QToolButton()
        self.edit_show_icon = QIcon(os.path.join(self.resource_path, "Icon", "eye_show_white.png"))
        self.edit_hide_icon = QIcon(os.path.join(self.resource_path, "Icon", "eye_hide_white.png"))
        self.edit_view_mode_btn.setIcon(self.edit_show_icon)
        self.edit_view_mode_btn.setIconSize(QSize(25, 25))
        self.edit_view_mode_btn.setFixedSize(30, 30)
        self.edit_view_mode_btn.setToolTip("View Mode")
        
        ## Table Widget
        self.edit_table_widget = QTableWidget()
        self.edit_table_headers = constants.EDIT_HEADERS
        
        ### Set table widget
        self.edit_table_widget.setSortingEnabled(True)
        self.edit_table_widget.setColumnCount(len(self.edit_table_headers))
        self.edit_table_widget.setHorizontalHeaderLabels(self.edit_table_headers)
        self.edit_table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        h_header = self.edit_table_widget.horizontalHeader()
        v_header = self.edit_table_widget.verticalHeader()
        h_header.setCascadingSectionResizes(False)
        h_header.setDefaultSectionSize(100)
        h_header.setStretchLastSection(True)
        v_header.setDefaultSectionSize(30)
        self.edit_table_widget.setColumnWidth(self.edit_table_headers.index("Render"), 60)
        self.edit_table_widget.setColumnWidth(self.edit_table_headers.index("Thumbnail"), 200)
        self.edit_table_widget.setColumnWidth(self.edit_table_headers.index("Scan Data"), 200)
        self.edit_table_widget.setColumnWidth(self.edit_table_headers.index("Version Description"), 180)
        self.edit_table_widget.setColumnWidth(self.edit_table_headers.index("First Frame Offset"), 150)
        self.edit_table_widget.setColumnWidth(self.edit_table_headers.index("End Frame Offset"), 150)

        # Buttons
        self.edit_h_spacer = QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.edit_validate_btn = QPushButton("Validate Version")
        self.edit_start_btn = QPushButton("Start")
        self.edit_start_btn.setFixedWidth(80)
        
    def __set_layout(self):
        self.setCentralWidget(self.tab_widget)
        self.__set_tab_1_layout()
        self.__set_tab_2_layout()
        
    def __set_tab_1_layout(self):
        # Set Tab 1
        self.plate_layout = QHBoxLayout()
        self.plate_sub_layout1 = QVBoxLayout()
        self.plate_sub_layout2 = QVBoxLayout()
        
        ## Sub Layout 1
        self.load_layout = QGridLayout()
        self.scan_folder_layout = QHBoxLayout()
        self.scan_folder_layout.addWidget(self.scan_folder_le)
        self.scan_folder_layout.addWidget(self.scan_folder_btn)
        
        self.excel_file_layout = QHBoxLayout()
        self.excel_file_layout.addWidget(self.excel_file_cmbx)
        self.excel_file_layout.addWidget(self.excel_file_load_btn)
        
        self.tool_layout = QHBoxLayout()
        self.tool_layout.addWidget(self.excel_file_create_btn)
        self.tool_layout.addItem(self.h_expander)
        self.tool_layout.addWidget(self.scan_folder_open_btn)
        self.tool_layout.addWidget(self.excel_file_open_btn)
        self.tool_layout.addWidget(self.scan_folder_reload_btn)
        self.tool_layout.addWidget(self.view_mode_btn)
        
        self.load_layout.addWidget(self.project_lb, 0, 0)
        self.load_layout.addWidget(self.project_cmbx, 0, 1)
        
        self.load_layout.addWidget(self.scan_folder_lb, 1, 0)
        self.load_layout.addLayout(self.scan_folder_layout, 1, 1)
        
        self.load_layout.addWidget(self.excel_file_lb, 2, 0)
        self.load_layout.addLayout(self.excel_file_layout, 2, 1)
        
        self.plate_sub_layout1.addLayout(self.load_layout)
        self.plate_sub_layout1.addWidget(self.h_divider)
        self.plate_sub_layout1.addLayout(self.tool_layout)
        self.plate_sub_layout1.addWidget(self.plate_table_widget)
        
        ## Sub Layout 2 - Render Settings
        self.render_group = QGroupBox("Render Settings")
        self.render_layout = QGridLayout()
        self.render_group.setLayout(self.render_layout)
        
        ### Export option
        self.render_export_layout = QHBoxLayout()
        self.render_export_layout.addWidget(self.render_export_exr)
        self.render_export_layout.addWidget(self.render_export_mov)
        self.render_export_layout.addWidget(self.render_export_jpg)
        self.render_export_layout.addWidget(self.render_export_png)
        self.render_layout.addWidget(self.render_export_lb, 0, 0)
        self.render_layout.addLayout(self.render_export_layout, 0, 1)
        
        ### FPS option
        self.render_fps_layout = QHBoxLayout()
        self.render_fps_layout.addWidget(self.render_fps_cmbx)
        self.render_fps_layout.addWidget(self.render_fps_spbx)
        self.render_layout.addWidget(self.render_fps_lb, 1, 0)
        self.render_layout.addLayout(self.render_fps_layout, 1, 1)
        
        ### Codec option
        self.render_layout.addWidget(self.render_codec_lb, 2, 0)
        self.render_layout.addWidget(self.render_codec_cmbx, 2, 1)
        
        ### Start Frame
        self.render_layout.addWidget(self.render_start_frame_lb, 3, 0)
        self.render_layout.addWidget(self.render_start_frame_spbx, 3, 1)
        
        ### Priority
        self.render_layout.addWidget(self.render_priority_lb, 4, 0)
        self.render_layout.addWidget(self.render_priority_spbx, 4, 1)
        
        self.plate_sub_layout2.addWidget(self.render_group)
        
        ## Sub Layout 2 - Apply Colorspace
        self.colorspace_group = QGroupBox("Colorspace")
        # self.colorspace_group.setFixedWidth(450)
        self.colorspace_layout = QGridLayout()
        self.colorspace_group.setLayout(self.colorspace_layout)
        
        ### Switch Colorspace
        self.colorspace_layout.addWidget(self.colorspace_switch_lb, 0, 0)
        self.colorspace_layout.addWidget(self.colorspace_switch_btn, 0, 1)
        
        ### OCIO Config
        self.ocio_path_layout = QHBoxLayout()
        self.ocio_path_layout.addWidget(self.colorspace_ocio_le)
        self.ocio_path_layout.addWidget(self.colorspace_ocio_btn)
        self.colorspace_layout.addWidget(self.colorspace_ocio_lb, 1, 0)
        self.colorspace_layout.addLayout(self.ocio_path_layout, 1, 1)
        
        ### Input Colorspace
        self.colorspace_layout.addWidget(self.colorspace_input_lb, 2, 0)
        self.colorspace_layout.addWidget(self.colorspace_input_cmbx, 2, 1)
        self.colorspace_layout.addWidget(self.colorspace_input_cmbx_nuke, 2, 1)
        
        ### Output Colorspace
        self.colorspace_layout.addWidget(self.colorspace_output_lb, 3, 0)
        self.colorspace_layout.addWidget(self.colorspace_output_cmbx, 3, 1)
        self.colorspace_layout.addWidget(self.colorspace_output_cmbx_nuke, 3, 1)
        
        ### LUT
        self.lut_layout = QHBoxLayout()
        self.lut_layout.addWidget(self.colorspace_cube_le)
        self.lut_layout.addWidget(self.colorspace_cube_btn)
        self.colorspace_layout.addWidget(self.colorspace_cube_lb, 4, 0)
        self.colorspace_layout.addLayout(self.lut_layout, 4, 1)
        
        self.plate_sub_layout2.addWidget(self.colorspace_group)
        
        ## Sub Layout 2 - Apply Resize
        self.resize_group = QGroupBox("Resize")
        self.resize_layout = QGridLayout()
        self.resize_group.setLayout(self.resize_layout)
        
        ### Resize Target
        self.target_layout = QHBoxLayout()
        self.target_layout.addWidget(self.resize_target_all_cb)
        self.target_layout.addWidget(self.resize_target_mov_cb)
        self.resize_layout.addWidget(self.resize_target_lb, 0, 0)
        self.resize_layout.addLayout(self.target_layout, 0, 1)
        
        ### Reformat
        self.reformat_layout = QHBoxLayout()
        self.reformat_layout.addWidget(self.render_reformat_cmbx)
        self.reformat_layout.addWidget(self.render_reformat_x_spbx)
        self.reformat_layout.addWidget(self.render_reformat_x_lb)
        self.reformat_layout.addWidget(self.render_reformat_y_spbx)
        self.resize_layout.addWidget(self.render_reformat_lb, 1, 0)
        self.resize_layout.addLayout(self.reformat_layout, 1, 1)
        
        ### Crop
        self.crop_layout = QHBoxLayout()
        self.crop_layout.addWidget(self.render_crop_cmbx)
        self.crop_layout.addWidget(self.render_crop_x_spbx)
        self.crop_layout.addWidget(self.render_crop_x_lb)
        self.crop_layout.addWidget(self.render_crop_y_spbx)
        self.resize_layout.addWidget(self.render_crop_lb, 2, 0)
        self.resize_layout.addLayout(self.crop_layout, 2, 1)
        
        ### Aspect Fit Mode
        self.resize_layout.addWidget(self.render_aspect_correction_lb, 3, 0)
        self.resize_layout.addWidget(self.render_aspect_fit_cmbx, 3, 1)
        
        self.plate_sub_layout2.addWidget(self.resize_group)
        
        ## Sub Layout 2 - Buttons
        self.plate_sub_layout2.addItem(self.v_spacer)
        
        self.btn_layout = QHBoxLayout()
        self.btn_layout.addWidget(self.validate_btn)
        self.btn_layout.addItem(self.h_spacer)
        self.btn_layout.addWidget(self.collect_btn)
        self.btn_layout.addWidget(self.render_btn)
        
        self.plate_sub_layout2.addLayout(self.btn_layout)
        
        # Set Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(QWidget())
        self.splitter.addWidget(QWidget())
        
        self.splitter.widget(0).setLayout(self.plate_sub_layout1)
        self.splitter.widget(1).setLayout(self.plate_sub_layout2)
        
        # Disable Right Side
        # self.splitter.widget(1).setDisabled(True)
        
        self.splitter.setSizes([1200, 400])
    
        self.plate_layout.addWidget(self.splitter)
        
        self.tab_plate.setLayout(self.plate_layout)
    
    def __set_tab_2_layout(self):
        # Set Tab 2
        self.edit_main_layout = QHBoxLayout()
        self.edit_layout = QVBoxLayout()
        
        self.edit_load_layout = QGridLayout()
        self.edit_scan_folder_layout = QHBoxLayout()
        self.edit_scan_folder_layout.addWidget(self.edit_scan_folder_le)
        self.edit_scan_folder_layout.addWidget(self.edit_scan_folder_btn)
        
        self.edit_excel_file_layout = QHBoxLayout()
        self.edit_excel_file_layout.addWidget(self.edit_excel_file_cmbx)
        self.edit_excel_file_layout.addWidget(self.edit_excel_file_load_btn)
        
        self.edit_tool_layout = QHBoxLayout()
        self.edit_tool_layout.addWidget(self.edit_excel_file_create_btn)
        self.edit_tool_layout.addWidget(self.edit_task_cmbx)
        self.edit_tool_layout.addItem(self.edit_h_expander)
        self.edit_tool_layout.addWidget(self.edit_scan_folder_open_btn)
        self.edit_tool_layout.addWidget(self.edit_excel_file_open_btn)
        self.edit_tool_layout.addWidget(self.edit_scan_folder_reload_btn)
        self.edit_tool_layout.addWidget(self.edit_view_mode_btn)
        
        self.edit_load_layout.addWidget(self.edit_project_lb, 0, 0)
        self.edit_load_layout.addWidget(self.edit_project_cmbx, 0, 1)
        
        self.edit_load_layout.addWidget(self.edit_scan_folder_lb, 1, 0)
        self.edit_load_layout.addLayout(self.edit_scan_folder_layout, 1, 1)
        
        self.edit_load_layout.addWidget(self.edit_excel_file_lb, 2, 0)
        self.edit_load_layout.addLayout(self.edit_excel_file_layout, 2, 1)
        
        self.edit_btn_layout = QHBoxLayout()
        self.edit_btn_layout.addItem(self.edit_h_spacer)
        self.edit_btn_layout.addWidget(self.edit_validate_btn)
        self.edit_btn_layout.addWidget(self.edit_start_btn)
        
        self.edit_layout.addLayout(self.edit_load_layout)
        self.edit_layout.addWidget(self.edit_h_divider)
        self.edit_layout.addLayout(self.edit_tool_layout)
        self.edit_layout.addWidget(self.edit_table_widget)
        self.edit_layout.addLayout(self.edit_btn_layout)
        
        self.edit_splitter = QSplitter(Qt.Horizontal)
        self.edit_splitter.addWidget(QWidget())
        
        self.edit_splitter.widget(0).setLayout(self.edit_layout)
        
        self.edit_main_layout.addWidget(self.edit_splitter)
        
        self.tab_edit.setLayout(self.edit_main_layout)
        
    def __set_stylesheet(self):
        self.setStyleSheet(
            "QToolButton {"
            "   border: 1px solid #444444;"
            "   border-radius: 4px;"
            "   background-color: rgb(63, 64, 66);"
            "   color: #dddddd;"
            "   height: 8px;"
            "}"
            "QToolButton:pressed {"
            "   border: 1px solid rgb(138, 180, 247);"
            "   background-color: rgb(63, 64, 66);"
            "}"
            "QToolButton:disabled {"
            "   background-color: rgb(63, 64, 66);"
            "   color: #888888;"
            "}"
            "QToolTip {"
            "   background-color: #444444;"
            "   color: #dddddd;"
            "   border: 1px solid #444444;"
            "   font-size: 10pt;"
            "}"
        )
    
    def __set_font(self):
        font_path = os.path.join(self.resource_path, "font", "Lato-Bold.ttf")
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

    def __set_menu_bar(self):
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        
        # set test menu
        # self.file_menu = self.menu_bar.addMenu("File")
        # self.view_menu = self.menu_bar.addMenu("View")
        # self.edit_menu = self.menu_bar.addMenu("Edit")
        # self.help_menu = self.menu_bar.addMenu("Help")
        self.user_menu = self.menu_bar.addMenu("Username")
        self.logout_action = self.user_menu.addAction("Logout")
        
        self.dev_menu = self.menu_bar.addMenu("Developer")
        self.log_action = self.dev_menu.addAction("Open Log File")
        self.log_clear_action = self.dev_menu.addAction("Clear Log File")

    def __set_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_bar.showMessage("Ready")
        
        
if __name__ == "__main__":
    app = QApplication([])
    io_manager = IOManager_UI()
    io_manager.setup_ui()
    io_manager.show()
    app.exec_()