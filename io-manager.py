# -*- coding: utf-8 -*-

import os
import re
import sys
import math
import shutil
import importlib
import traceback
from datetime import datetime

# Add Custom Modules Path
sys.path.append((os.path.join(os.path.dirname(__file__), "pymodules")).replace("/", os.sep))

import Imath
import OpenEXR
import pydpx_meta
from PySide2.QtCore import Qt, QThreadPool, QSettings
from PySide2.QtCore import QObject, Signal, QRunnable
from PySide2.QtGui import QColor, QPixmap
from PySide2.QtWidgets import ( QMessageBox, QFileDialog, QApplication,
                               QTableWidgetItem, QWidget, QHBoxLayout,
                               QCheckBox, QLabel, QMenu,
                               QStyledItemDelegate, QComboBox )
from timecode import Timecode

# Custom Modules
import pymodules.ui as ui
import pymodules.constants as constants
import pymodules.sg_manager as sg_manager
import pymodules.nuke_manager as nuke_manager
import pymodules.excel_manager as excel_manager
import pymodules.ffmpeg_manager as ffmpeg_manager
import pymodules.deadline_manager as deadline_manager
import pymodules.login_dialog as login_dialog
import pymodules.progress_dialog as progress_dialog
import pymodules.loding_dialog as loading_dialog
import pymodules.init_logger as init_logger

# Set Logger
logger = init_logger.IOManagerLogger(os.path.basename(__file__), constants.LOG_PATH)


class IOManager(ui.IOManager_UI):
    def __init__(self):
        super(IOManager, self).__init__()
        if self.check_user():
            self.setup_ui()
            self.check_dev_mode()
            self.__vars()
            self.populate_projects()
            self.populate_data()
            self.__connections()
            self.load_settings()

            ### Temporary Disable ###
            self.collect_btn.setDisabled(True)

    def check_user(self):
        _login_dialog = login_dialog.LoginDialog()
        login_success, self.user_data = _login_dialog.exec_()
        if not login_success:
            return False
        return True
        
    def check_dev_mode(self):
        try:
            pc_name = os.getlogin()
            if not pc_name.startswith("TD"):
                self.dev_menu.hide()
                logger.disable_stream_handler()
            else:
                logger.info("Running in Developer Mode")
                pass
        except:
            self.dev_menu.hide()
            
        self.user_menu.setTitle(self.user_data.get('email'))
        
    def __vars(self):
        # flags
        self.__simple_view = False
        self.__is_sequence = False
        self.__use_nuke_colorspace = False
        self.__is_edit = False
        
        # str
        self.__error_paths = ""
        
        # dict
        self.__missing_thumnails = {}
        self.__edit_missing_thumnails = {}
        
        # constants
        self.headers = constants.HEADERS
        self.edit_headers = constants.EDIT_HEADERS
        self.headers_ignore = constants.IGNORE_HEADERS
        self.headers_readonly_excel = constants.READONLY_HEADERS
        self.headers_readonly_table = constants.READONLY_CELL_HEADERS
        self.seq_types = constants.SEQUENCE_TYPES
        self.default_drive = constants.DEFAULT_DRIVE
        self.default_ocio_config = constants.DEFAULT_OCIO_CONFIG
        self.default_slate = constants.DEFAULT_SLATE
        self.log_path = constants.LOG_PATH
        self.uploaded_version_status = constants.UPLOADED_VERSION_STATUS
        
        # modules
        self.loading_dialog = loading_dialog.LoadingDialog("Loading...", self)
        self.processing_dialog = loading_dialog.LoadingDialog("Processing...", self)
        self.excel_manager = excel_manager.ExcelManager()
        self.ffmpeg_io = ffmpeg_manager.FFMPEGManager()
        self.deadline_manager = deadline_manager.DeadlineManager(self.user_data.get('email'))
    
    def __connections(self):
        # Tab
        self.tab_widget.currentChanged.connect(self.tab_changed)

        ## Plate
        # Load
        self.project_cmbx.currentIndexChanged.connect(self.populate_data)
        self.scan_folder_btn.clicked.connect(self.scan_folder)
        self.excel_file_load_btn.clicked.connect(self.load_excel_file)
        
        # Tools
        self.excel_file_create_btn.clicked.connect(self.create_excel_file)
        self.scan_folder_open_btn.clicked.connect(self.open_scan_folder)
        self.excel_file_open_btn.clicked.connect(self.open_excel_file)
        self.scan_folder_reload_btn.clicked.connect(self.reload_scan_folder)
        self.view_mode_btn.clicked.connect(lambda: self.change_view_mode(self.__simple_view))
        
        # Table
        self.plate_table_widget.customContextMenuRequested.connect(self.table_context_menu)
        self.plate_table_widget.itemChanged.connect(self.table_item_changed)
        
        # Render Settings
        self.render_fps_cmbx.currentIndexChanged.connect(self.fps_changed)
        self.render_start_frame_spbx.valueChanged.connect(self.start_frame_changed)
        
        # Colorspace
        self.colorspace_switch_btn.clicked.connect(self.switch_colorspace)
        self.colorspace_ocio_btn.clicked.connect(self.browse_ocio_config)
        self.colorspace_cube_btn.clicked.connect(self.browse_cube_dir)
        
        # Apply Resize
        self.resize_target_all_cb.stateChanged.connect(self.target_check_toggle)
        self.resize_target_mov_cb.stateChanged.connect(self.target_check_toggle)
        
        self.render_reformat_cmbx.currentIndexChanged.connect(self.reformat_changed)
        self.render_crop_cmbx.currentIndexChanged.connect(self.crop_changed)
        
        # Buttons
        self.validate_btn.clicked.connect(self.validate_version)
        self.collect_btn.clicked.connect(self.collect_files)
        self.render_btn.clicked.connect(self.start_plate_handler)
        
        ## Edit
        # Load
        self.edit_project_cmbx.currentIndexChanged.connect(lambda: self.project_cmbx.setCurrentIndex(self.edit_project_cmbx.currentIndex()))
        self.edit_scan_folder_btn.clicked.connect(self.edit_scan_folder)
        self.edit_excel_file_load_btn.clicked.connect(self.load_excel_file)
        
        # Tools
        self.edit_excel_file_create_btn.clicked.connect(self.create_edit_excel_file)
        self.edit_task_cmbx.currentIndexChanged.connect(self.toggle_edit_type)
        self.edit_scan_folder_open_btn.clicked.connect(self.open_scan_folder)
        self.edit_excel_file_open_btn.clicked.connect(self.open_excel_file)
        self.edit_scan_folder_reload_btn.clicked.connect(self.reload_scan_folder)
        self.edit_view_mode_btn.clicked.connect(lambda: self.change_view_mode(self.__simple_view))
        
        # Table
        self.edit_table_widget.customContextMenuRequested.connect(self.table_context_menu)
        self.edit_table_widget.itemChanged.connect(self.edit_table_item_changed)
        
        # Buttons
        self.edit_validate_btn.clicked.connect(self.validate_version)
        self.edit_start_btn.clicked.connect(self.start_edit_handler)
        
        ## Menu
        self.logout_action.triggered.connect(self.logout)
        self.log_action.triggered.connect(self.open_log_file)
        self.log_clear_action.triggered.connect(self.clear_log_file)
        
    def tab_changed(self, index):
        self.status_bar.clearMessage()
        self.status_bar.setStyleSheet("background-color: transparent")
        if index == 0:
            self.__is_edit = False
        elif index == 1:
            self.__is_edit = True
    
    def target_check_toggle(self):
        sender = self.sender()

        if sender == self.resize_target_all_cb:
            if self.resize_target_all_cb.isChecked():
                self.resize_target_mov_cb.blockSignals(True)
                self.resize_target_mov_cb.setChecked(False)
                self.resize_target_mov_cb.blockSignals(False)
                self.set_plate_resolution()

        elif sender == self.resize_target_mov_cb:
            if self.resize_target_mov_cb.isChecked():
                self.resize_target_all_cb.blockSignals(True)
                self.resize_target_all_cb.setChecked(False)
                self.resize_target_all_cb.blockSignals(False)
                self.set_plate_resolution()

    # Decorator
    def disconnect_table_event(func):
        def wrapper(self, *args, **kwargs):
            try:
                self.plate_table_widget.itemChanged.disconnect()
                self.edit_table_widget.itemChanged.disconnect()
            except:
                pass
            try:
                val = func(self, *args, **kwargs)
            finally:
                self.plate_table_widget.itemChanged.connect(self.table_item_changed)
                self.edit_table_widget.itemChanged.connect(self.edit_table_item_changed)
            return val 
        return wrapper
    
    def populate_projects(self):
        try:
            projects = sg_manager.get_active_projects()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"ShotGrid에서 프로젝트를 가져오는 중 오류가 발생했습니다:\n{e}")
            logger.error(traceback.format_exc())
            return
            
        if not projects:
            logger.error("No active projects found in ShotGrid.")
            return
        
        self.project_cmbx.clear()
        self.project_cmbx.addItems(projects)
        self.edit_project_cmbx.clear()
        self.edit_project_cmbx.addItems(projects)
    
    def populate_data(self):
        current_project = self.project_cmbx.currentText()
        if not current_project:
            QMessageBox.warning(self, "Warning", "프로젝트를 선택해주세요.")
            return
        
        self.edit_project_cmbx.setCurrentIndex(self.project_cmbx.currentIndex())
        
        # Get Project data from ShotGrid
        try:
            data = sg_manager.get_project_data(current_project)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"ShotGrid에서 프로젝트 데이터를 가져오는 중 오류가 발생했습니다:\n{e}")
            logger.error(traceback.format_exc())
            return
        
        if not data:
            QMessageBox.warning(self, "Warning", "프로젝트 데이터를 찾을 수 없습니다.")
            logger.error(f"Project data not found for {current_project}")
            return
        
        # Set FPS
        fps = data.get("sg_mov_fps", None)
        if fps:
            self.render_fps_cmbx.setCurrentText("Custom")
            self.render_fps_spbx.setValue(float(fps))
        else:
            logger.warning("FPS not found in ShotGrid. Setting to 23.976")
            self.render_fps_cmbx.setCurrentText("23.976")
            self.render_fps_spbx.setValue(23.976)
            
        # Set Codec
        codec = data.get("sg_mov_codec", None)
        if codec and self.render_codec_cmbx.findText(codec) != -1:
            self.render_codec_cmbx.setCurrentText(codec)
        else:
            logger.warning("Codec not found in ShotGrid. Setting to ProRes 4:2:2 Proxy 10-bit")
            self.render_codec_cmbx.setCurrentText("ProRes 4:2:2 Proxy 10-bit")
            
        # Set OCIO
        ocio = data.get("sg_ocio", False)
        self.__use_nuke_colorspace = not ocio
        if ocio and self.colorspace_switch_btn.text() == "Use OCIO Config":
            self.colorspace_switch_btn.click()
        elif not ocio and self.colorspace_switch_btn.text() == "Use Nuke Default":
            self.colorspace_switch_btn.click()
        
        # Set OCIO Path
        ocio_path = data.get("sg_ocio_path", None)
        if not ocio_path:
            logger.warning("OCIO Path not found in ShotGrid. Setting to Default OCIO Config")
            self.colorspace_ocio_le.setText(self.default_ocio_config)
        else:        
            self.colorspace_ocio_le.setText(ocio_path.replace(os.sep, "/"))
            
            cube_path = os.path.join(os.path.dirname(ocio_path), "luts")
            if os.path.exists(cube_path):
                self.colorspace_cube_le.setText(cube_path.replace(os.sep, "/"))
            
        # Set Input Colorspace
        input_colorspace = data.get("sg_exr_color_space", None)
        if input_colorspace and input_colorspace in self.colorspace_input_cmbx.color_list:
            self.colorspace_input_cmbx.set_combo_text(input_colorspace)
        else:
            self.colorspace_input_cmbx.setText("Select Colorspace")
            self.colorspace_input_cmbx_nuke.setCurrentText(input_colorspace)
            
        # Set Output Colorspace
        output_colorspace = data.get("sg_mov_color_space", None)
        if output_colorspace and output_colorspace in self.colorspace_output_cmbx.color_list:
            self.colorspace_output_cmbx.set_combo_text(output_colorspace)
        else:
            self.colorspace_output_cmbx.setText("Select Colorspace")
            self.colorspace_output_cmbx_nuke.setCurrentText(output_colorspace)
            
        # Set Exr Resolution
        exr_resolution = data.get("sg_exr_resolution", None)
        if not exr_resolution:
            exr_resolution = "3840*2160"
            
        # Reset Previous Data
        self.scan_folder_le.clear()
        self.excel_file_cmbx.clear()
        self.plate_table_widget.clearContents()
        self.plate_table_widget.setRowCount(0)
        self.__missing_thumnails = {}
        self.__is_sequence = False
        
        if self.__is_edit:
            self.edit_scan_folder_le.clear()
            self.edit_excel_file_cmbx.clear()
            self.edit_table_widget.clearContents()
            self.edit_table_widget.setRowCount(0)
            self.__edit_missing_thumnails = {}
        
        # Set Status Message
        msg = f"Project: {current_project} | "
        msg += f"FPS: {fps} | "
        msg += f"Codec: {codec} | "
        msg += f"OCIO: {ocio} | "
        msg += f"OCIO Path: {ocio_path} | "
        msg += f"Input Colorspace: {input_colorspace} | "
        msg += f"Output Colorspace: {output_colorspace} | "
        msg += f"Resolution: {exr_resolution}"
        self.status_bar.showMessage(msg)
        
    def edit_scan_folder(self):
        if not self.edit_scan_folder_le.text():
            data_root = f"{self.default_drive}{self.edit_project_cmbx.currentText()}/stuff/ftp"
        else:
            data_root = self.edit_scan_folder_le.text()
            
        directory = data_root if os.path.exists(data_root) else self.default_drive
        folder = QFileDialog.getExistingDirectory(
            self, "Select Scan Folder", directory, ~QFileDialog.ShowDirsOnly
            )
        
        if not folder:
            return
        
        if not folder.startswith(f"{self.default_drive}{self.edit_project_cmbx.currentText()}"):
            QMessageBox.warning(self, "Warning", "선택된 프로젝트의 스캔 폴더가 아닙니다.")
            return
        
        self.edit_scan_folder_le.setText(folder)
        
        try:
            self.load_edit_data(folder)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"데이터를 불러오는 중 오류가 발생했습니다:\n{e}")
            logger.error(traceback.format_exc())
            return
        
        if not self.__edit_missing_thumnails:
            self.reload_excel_list(folder)
        
    def scan_folder(self):
        if not self.scan_folder_le.text():
            data_root = f"{self.default_drive}{self.project_cmbx.currentText()}/stuff/scan"
        else:
            data_root = self.scan_folder_le.text()
            
        directory = data_root if os.path.exists(data_root) else self.default_drive
        folder = QFileDialog.getExistingDirectory(
            self, "Select Scan Folder", directory, ~QFileDialog.ShowDirsOnly
            )
        
        if not folder:
            return
        
        if not folder.startswith(f"{self.default_drive}{self.project_cmbx.currentText()}"):
            QMessageBox.warning(self, "Warning", "선택된 프로젝트의 스캔 폴더가 아닙니다.")
            return
        
        self.scan_folder_le.setText(folder)
        self.populate_cube_files()
        
        # Load Data
        try:
            self.load_data(folder)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"데이터를 불러오는 중 오류가 발생했습니다:\n{e}")
            logger.error(traceback.format_exc())
            return
        
        if not self.__missing_thumnails:
            self.reload_excel_list(folder)
            
    def reload_scan_folder(self):
        if self.__is_edit:
            folder = self.edit_scan_folder_le.text()
            table = self.edit_table_widget
            missing_thumnails = self.__edit_missing_thumnails
        else:
            folder = self.scan_folder_le.text()
            table = self.plate_table_widget
            missing_thumnails = self.__missing_thumnails
            
        if not folder:
            QMessageBox.warning(self, "Warning", "스캔 폴더를 선택해주세요.")
            return
        
        # init table
        table.clearContents()
        table.setRowCount(0)
        
        # load data
        if self.__is_edit:
            try:
                self.load_edit_data(folder)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"데이터를 불러오는 중 오류가 발생했습니다:\n{e}")
                logger.error(traceback.format_exc())
                return
        else:
            try:
                self.load_data(folder)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"데이터를 불러오는 중 오류가 발생했습니다:\n{e}")
                logger.error(traceback.format_exc())
                return
        
        if not missing_thumnails:
            self.reload_excel_list(folder)
            
    def reload_excel_list(self, folder):
        excel_list = self.set_excel_list(folder)
        if not excel_list:
            return
        
        ask = QMessageBox.question(self, "Excel Files Found", f"엑셀 파일이 존재합니다. 불러오시겠습니까?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ask == QMessageBox.Yes:
            self.load_excel_file()
    
    @disconnect_table_event  
    def load_data(self, data_root): 
        # Show Loading Dialog
        self.loading_dialog.show()
        QApplication.processEvents()
        
        # set ascending order for scan data
        self.plate_table_widget.sortItems(self.headers.index("Scan Data"), Qt.AscendingOrder)
        self.plate_table_widget.clearContents()
        self.plate_table_widget.setRowCount(0)
        
        # Clear Vars
        self.__missing_thumnails = {}
        self.__is_sequence = False
        
        # Check if data is sequence or mov
        logger.debug(f"Checking if data is sequence or mov in {data_root}")
        self.__is_sequence = self.load_sequence_data(data_root)
        print(f"Is Sequence: {self.__is_sequence}")
        if not self.__is_sequence:
            logger.debug(f"Data is not sequence. Loading mov data in {data_root}")
            self.load_mov_data(data_root)
        
        logger.debug(f"Data loaded in {data_root}, data type: {'Sequence' if self.__is_sequence else 'MOV'}")
        self.parse_scan_data()
            
        # Set NoneType data's to empty string
        for row in range(self.plate_table_widget.rowCount()):
            for col in range(self.plate_table_widget.columnCount()):
                item = self.plate_table_widget.item(row, col)
                if not item:
                    self.plate_table_widget.setItem(row, col, QTableWidgetItem(""))
                    
        # Set Sub-Layout Enabled
        self.splitter.widget(1).setDisabled(False)
        
        self.loading_dialog.hide()
        self.start_frame_changed()
        
        return self.__missing_thumnails
    
    @disconnect_table_event
    def load_edit_data(self, data_root):
        # Show Loading Dialog
        self.loading_dialog.show()
        QApplication.processEvents()
        
        # set ascending order for scan data
        self.edit_table_widget.sortItems(self.edit_headers.index("Scan Data"), Qt.AscendingOrder)
        self.edit_table_widget.clearContents()
        self.edit_table_widget.setRowCount(0)
        
        # Clear Vars
        self.__edit_missing_thumnails = {}
        
        self.load_mov_data(data_root)
            
        # Set NoneType data's to empty string
        for row in range(self.edit_table_widget.rowCount()):
            for col in range(self.edit_table_widget.columnCount()):
                item = self.edit_table_widget.item(row, col)
                if not item:
                    self.edit_table_widget.setItem(row, col, QTableWidgetItem(""))
                    
        self.loading_dialog.hide()
        
        return self.__edit_missing_thumnails
    
    @disconnect_table_event
    def parse_scan_data(self):
        if self.__is_edit:
            table = self.edit_table_widget
            headers = self.edit_headers
        else:
            table = self.plate_table_widget
            headers = self.headers
        
        # each row, parse scan data to get shot name and type
        pattern = r"^([A-Z0-9_]+)_(mp\d|sp\d|rp\d)_(v\d{3})"  # ex) "A01_001_mp0_v001", "A01_001_sp0_v001", "A01_001_rp0_v001"
        for row in range(table.rowCount()):
            scan_data = table.item(row, headers.index("Scan Data")).text()
            match = re.match(pattern, scan_data)
            
            if not match:
                logger.warning(f"Scan Data not in correct format: {scan_data}")
                continue
            
            try:
                shot_name, _type, version = match.groups()
                sequence = shot_name.split("_")[0]
            except:
                logger.warning(f"Error parsing Scan Data: {scan_data}")
                continue
            
            table.setItem(row, headers.index("Sequence"), QTableWidgetItem(sequence))
            table.setItem(row, headers.index("Shot Name"), QTableWidgetItem(shot_name))
            if not self.__is_edit:
                table.setItem(row, headers.index("Type"), QTableWidgetItem(_type))
            
    def populate_cube_files(self):
        self.plate_table_widget.setItemDelegateForColumn(self.headers.index("Cube"), None)
            
        cube_dir = self.colorspace_cube_le.text()
        if not cube_dir:
            return
        cube_files = [f for f in os.listdir(cube_dir) if f.endswith(".cube")]
        
        self.plate_table_widget.setItemDelegateForColumn(self.headers.index("Cube"), CustomDelegate(self, cube_files, "None"))
        
        for row in range(self.plate_table_widget.rowCount()):
            self.plate_table_widget.setItem(row, self.headers.index("Cube"), QTableWidgetItem("None"))
    
    @disconnect_table_event
    def load_mov_data(self, data_root):
        if self.__is_edit:
            table = self.edit_table_widget
            headers = self.edit_headers
            missing_thumnails = self.__edit_missing_thumnails
        else:
            table = self.plate_table_widget
            headers = self.headers
            missing_thumnails = self.__missing_thumnails
        
        data_path_list = [
            path for path in os.listdir(data_root) if path.lower().endswith(".mov")
        ]
        data_path_list.sort()
        
        if not data_path_list:
            return
        
        table.setRowCount(len(data_path_list))
        
        # Set Items
        for idx, file_name in enumerate(data_path_list):
            # Set 'Render' Column
            render_widget = QWidget()
            render_layout = QHBoxLayout(render_widget)
            render_layout.setAlignment(Qt.AlignCenter)
            render_layout.setContentsMargins(0, 0, 0, 0)
            render_ckbx = QCheckBox()
            render_ckbx.setChecked(True)
            render_ckbx.setStyleSheet("QCheckBox::indicator { margin-left: 8; margin-right: 0; }")
            render_layout.addWidget(render_ckbx)
            table.setCellWidget(idx, headers.index("Render"), render_widget)
            
            # Set 'Scan Data' Column
            scan_data_item = QTableWidgetItem(os.path.splitext(file_name)[0])
            self.set_read_only_cells(idx, "Scan Data", scan_data_item)
            
            # Get Metadata
            data_path = os.path.join(data_root, file_name)
            metadata = self.ffmpeg_io.extract_mov_metadata(data_path)
            self.set_clip_name_column(idx, data_path, ext="mov")

            if self.__is_edit:
                type_item = QTableWidgetItem(self.edit_task_cmbx.currentText())
                self.set_read_only_cells(idx, "Type", type_item)
                
                # get datetime to YYMMDD
                date_item = QTableWidgetItem(datetime.now().strftime("%y%m%d"))
                table.setItem(idx, headers.index("Date"), date_item)
            
            if metadata:
                start_timecode = metadata.get("start_tc", None)
                duration = metadata.get("duration", None)
                fps = metadata.get("fps", None)
                end_timecode = metadata.get("end_tc", None)

                self.set_plate_resolution(idx, metadata)

                start_frame = 1001
                
                # Set 'Frame' Columns
                if not duration:
                    continue
                end_frame = start_frame + duration - 1

                if not start_frame or not end_frame:
                    continue
                self.set_frame_columns(idx, start_frame, end_frame)
                
                # Set 'TimeCode' Columns
                if not start_timecode or not end_timecode:
                    continue
                
                if not self.__is_edit:
                    self.set_timecode_item(idx, headers.index("TimeCode In"), start_timecode)
                    self.set_timecode_item(idx, headers.index("TimeCode Out"), end_timecode)
                    
            # Set 'Thumbnail' Column
            thumb_name = os.path.basename(data_path).replace(".mov", ".jpg")
            thumb_path = os.path.join(data_root, "_io", "proxy_thumb", thumb_name).replace("/", os.sep)
            
            self.ensure_dir_exists(os.path.dirname(thumb_path))
                
            if not os.path.exists(thumb_path):
                missing_thumnails[idx] = data_path, thumb_path
                continue
            else:
                self.set_thumbnail_column(idx, thumb_path)
        
        # Generate Missing Thumbnails
        if missing_thumnails:
            self.run_thumb_thread(missing_thumnails)
                        
        # Set Row Height
        for row in range(table.rowCount()):
            table.setRowHeight(row, 120)
    
    def set_plate_resolution(self, idx=None, metadata=None):
        if self.__is_edit:
            return

        if not idx and not metadata:
            reformat_resolution = self.get_reformat_resolution()
            if not reformat_resolution:
                return
            for idx in range(self.plate_table_widget.rowCount()):
                self.set_read_only_cells(idx, "Plate Resolution", QTableWidgetItem(reformat_resolution))
            return

        width = metadata.get("width", None)
        height = metadata.get("height", None)
        self.org_resolution = f"{width}*{height}"
        if not self.org_resolution:
            return
        self.set_read_only_cells(idx, "Plate Resolution", QTableWidgetItem(self.org_resolution))

    def set_sequence_plate_resolution_column(self, idx, first_frame_path):

        exr_file = OpenEXR.InputFile(first_frame_path)
        dw = exr_file.header()['dataWindow']
        width = dw.max.x - dw.min.x + 1
        height = dw.max.y - dw.min.y + 1
        self.org_resolution = f"{width}*{height}"

        if not self.org_resolution:
            return
        self.set_read_only_cells(idx, "Plate Resolution", QTableWidgetItem(self.org_resolution))

    def get_reformat_resolution(self):

        if not self.resize_target_all_cb.isChecked():
            return self.org_resolution

        if self.render_reformat_cmbx.currentText() == "Original":
            return self.org_resolution
    
        width = self.render_reformat_x_spbx.value()
        height = self.render_reformat_y_spbx.value()
        resolution = f"{width}*{height}"

        return resolution

    @disconnect_table_event
    def load_sequence_data(self, data_root):
        sequence_loaded = False
        data_path_list = [
            path for path in os.listdir(data_root) if os.path.isdir(os.path.join(data_root, path))
            and path not in ["_io", "xml", "@eaDir", "proxy_thumb"]
        ]
        data_path_list.sort()

        if not data_path_list:
            logger.debug(f"No sequence data found in {data_root}")
            print(sequence_loaded)
            return sequence_loaded
        
        self.plate_table_widget.setRowCount(len(data_path_list))
        logger.debug(f"Sequence data found in {data_root}")
        # Set Items
        for idx, data_path in enumerate(data_path_list):
            logger.debug(f"Loading sequence data: {data_path}")
            # Set 'Render' Column
            render_widget = QWidget()
            render_layout = QHBoxLayout(render_widget)
            render_layout.setAlignment(Qt.AlignCenter)
            render_layout.setContentsMargins(0, 0, 0, 0)
            render_ckbx = QCheckBox()
            render_ckbx.setChecked(True)
            render_ckbx.setStyleSheet("QCheckBox::indicator { margin-left: 8; margin-right: 0; }")
            render_layout.addWidget(render_ckbx)
            self.plate_table_widget.setCellWidget(idx, self.headers.index("Render"), render_widget)
            
            # Set 'Scan Data' Column
            scan_data_item = QTableWidgetItem(data_path)
            self.set_read_only_cells(idx, "Scan Data", scan_data_item)

            # Get Image Sequence
            sequence_info = self.check_image_sequence(os.path.join(data_root, data_path))
            if not sequence_info:
                logger.debug(f"Failed to Check Sequence in {data_path}")
                continue
                
            start_frame, end_frame, frame_to_path = sequence_info
            start_frame_path, end_frame_path = frame_to_path[int(start_frame)], frame_to_path[int(end_frame)]
            if not start_frame or not end_frame:
                logger.debug(f"Could not find start or end frame in {data_path}")
                continue

            # Set 'Clip Name' Column
            self.set_clip_name_column(idx, start_frame_path, ext="exr")

            # Set 'Plate Resolution' Column
            self.set_sequence_plate_resolution_column(idx, start_frame_path)

            # Set 'Frame' Columns
            logger.debug(f"Setting Frame Columns: {start_frame} - {end_frame}")
            self.set_frame_columns(idx, start_frame, end_frame)

            # Set 'TimeCode' Columns
            logger.debug(f"Setting TimeCode Columns: {start_frame_path} - {end_frame_path}")
            self.set_timecode_columns(idx, start_frame_path, end_frame_path)
            
            # Set 'Thumbnail' Column
            seq_path = os.path.dirname(start_frame_path).replace("/", os.sep)
            seq_name = os.path.basename(seq_path)
            thumb_path = os.path.join(seq_path, "proxy_thumb", f"{seq_name}.jpg").replace("/", os.sep)
            
            self.ensure_dir_exists(os.path.dirname(thumb_path))
                
            if not os.path.exists(thumb_path):
                self.__missing_thumnails[idx] = start_frame_path.replace("/", os.sep), thumb_path
                logger.debug(f"Thumbnail not found in {data_path}")
                continue
            else:
                self.set_thumbnail_column(idx, thumb_path)
                
        sequence_loaded = True

        # Generate Missing Thumbnails
        if self.__missing_thumnails:
            self.run_thumb_thread(self.__missing_thumnails)
        
        # Set Row Height
        for row in range(self.plate_table_widget.rowCount()):
            self.plate_table_widget.setRowHeight(row, 120)  
        result = sequence_loaded if sequence_loaded else False

        return result
    
    def set_clip_name_column(self, idx, path, ext=None):
        if self.__is_edit:
            return

        clip_name = None
        if ext == "mov":
            clip_name = self.ffmpeg_io.extract_mov_clip_name(path)

            if not clip_name:
                clip_name = os.path.basename(os.path.dirname(path))

            clip_name_item = QTableWidgetItem(str(clip_name))
            self.set_read_only_cells(idx, "Clip Name", clip_name_item)

        elif ext == "exr":
            exr_file = OpenEXR.InputFile(path)
            header = exr_file.header()

            clip_names = []
            filmlight = "uk.ltd.filmlight.Clip"
            cameraClipName = "interim.clip.cameraClipName"
            if filmlight in header or cameraClipName in header:
                try:
                    filmlight = os.path.splitext(header.get(filmlight))[0]
                    if isinstance(filmlight, bytes):
                        filmlight = filmlight.decode("utf-8", errors="ignore")
                    clip_names.append(filmlight)

                except Exception as e:
                    filmlight = ""

                try:
                    cameraClipName = os.path.splitext(header.get(cameraClipName))[0]
                    if isinstance(cameraClipName, bytes):
                        cameraClipName = cameraClipName.decode("utf-8", errors="ignore")
                    clip_names.append(cameraClipName)

                except Exception as e:
                    cameraClipName = ""

                if not filmlight and not cameraClipName:
                    clip_name = os.path.basename(os.path.dirname(path))
                    clip_names.append(clip_name)
            else:
                clip_name = os.path.basename(os.path.dirname(path))
                clip_names.append(clip_name)

            default_val = cameraClipName if cameraClipName else (filmlight if filmlight else "None")

            item = QTableWidgetItem(default_val)
            item.setData(Qt.UserRole, clip_names)
            self.plate_table_widget.setItem(idx, self.headers.index("Clip Name"), item)

            self.plate_table_widget.setItemDelegateForColumn(self.headers.index("Clip Name"), CustomDelegate(self.plate_table_widget, clip_names, default_val))

            for row in range(self.plate_table_widget.rowCount()):
                if not self.plate_table_widget.item(row, self.headers.index("Clip Name")):
                    clip_name_item = QTableWidgetItem("None")
                    self.set_read_only_cells(row, "Clip Name", clip_name_item)

    def run_thumb_thread(self, missing_thumbnails):
        self.progress_dialog = progress_dialog.ProgressDialog("Generating Thumbnails...", len(missing_thumbnails), self)
        self.progress_dialog.show()

        self.workers = []
        self.thread_pool = QThreadPool.globalInstance()
        self.__error_paths = ""

        self.result = {}
        self.progress_count = 0

        for row, (input_path, output_path) in missing_thumbnails.items():
            worker = ThumbnailWorker(row, input_path, output_path, ffmpeg_manager.FFMPEGManager())
            worker.signals.succeeded.connect(self.worker_succeeded)
            worker.signals.error_occurred.connect(self.worker_error)

            self.workers.append(worker)
            self.thread_pool.start(worker)

    def worker_succeeded(self, row, thumb_path):
        self.result[row] = thumb_path
        self.progress_count += 1
        self.progress_dialog.progress_bar.setValue(self.progress_count)
        
        if self.progress_count == len(self.workers):
            self.progress_dialog.close()
            for row, thumb_path in self.result.items():
                self.set_thumbnail_column(row, thumb_path)
                
    def worker_error(self, row, error_path):
        self.__error_paths += f"{error_path}\n"
        logger.error(f"Thread Error: {error_path}")

        if self.progress_count == len(self.workers):
            self.progress_dialog.close()
            QMessageBox.critical(self, "Error", f"Thumbnail 생성 중 오류가 발생했습니다:\n{self.__error_paths}")
            logger.error(f"Errors occurred:\n{self.__error_paths}")

    def update_progress(self, value):
        self.progress_dialog.progress_bar.setValue(value)
                    
    def set_excel_list(self, folder):
        if self.__is_edit:
            excel_cmbx = self.edit_excel_file_cmbx
            excel_load_btn = self.edit_excel_file_load_btn
        else:
            excel_cmbx = self.excel_file_cmbx
            excel_load_btn = self.excel_file_load_btn
        
        data_root = folder
        excel_list = [f for f in os.listdir(data_root) if f.endswith(".xlsx") and f[0] != "~"]
        excel_list.sort(reverse=True)
        excel_cmbx.clear()
        
        if not excel_list:
            excel_cmbx.addItem("No Excel Files Found")
            excel_load_btn.setDisabled(True)
            return None
        
        excel_cmbx.addItems(excel_list)
        excel_load_btn.setDisabled(False)
        
        return excel_list
    
    def check_image_sequence(self, folder) -> tuple:
        if not os.path.exists(folder):
            return set()
        
        image_files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        
        supported_files = [f for f in image_files if f.endswith(tuple(self.seq_types))]
        
        if not supported_files:
            return set()

        pattern = re.compile(r"(.+?)(\d+)(\.\w+)$")
        frame_numbers = []
        frame_to_path = {}
        
        for f in supported_files:
            match = pattern.match(f)
            if match:
                frame_number = match.group(2)
                frame_numbers.append(frame_number)
                frame_to_path[int(frame_number)] = os.path.join(folder, f).replace(os.sep, "/")

        # if no frame numbers found, return None for frames
        if not frame_numbers:
            return set()

        # if only one frame found, return the frame number and path
        try:
            if len(frame_numbers) == 1:
                single_frame_path = frame_to_path[frame_numbers[0]]
                return (frame_numbers[0], frame_numbers[0], single_frame_path)
        except Exception as e:
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", "스캔 폴더에 이미지 시퀀스가 아닌 파일이 있습니다.")
            return set()

        frame_numbers.sort(key=int)

        # check for missing frames
        missing_frame_paths = []
        for i in range(len(frame_numbers) - 1):
            if int(frame_numbers[i+1]) != int(frame_numbers[i]) + 1:
                missing_frame_paths.append(folder)

        # if missing frames found, show a warning message and return None for frames
        if missing_frame_paths:
            msg = "\n".join(missing_frame_paths)
            QMessageBox.critical(self, "Error", f"이미지 시퀀스에 누락된 프레임이 있습니다:\n{msg}")
            logger.warning(f"Missing frames found in {missing_frame_paths}")
            return None

        if frame_numbers:
            start_frame = min(frame_numbers)
            end_frame = max(frame_numbers)
            return (start_frame, end_frame, frame_to_path)
        
        return set()
        
    def set_read_only_cells(self, row, col_name, item):
        if self.__is_edit:
            table = self.edit_table_widget
            headers = self.edit_headers
        else:
            table = self.plate_table_widget
            headers = self.headers
        
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setBackgroundColor(QColor(30, 30, 30))
        table.setItem(row, headers.index(col_name), item)
            
    def set_frame_columns(self, row, start_frame, end_frame):
        if not start_frame or not end_frame:
            return
        
        # Set 'Start Frame' Column
        start_frame_item = QTableWidgetItem(str(int(start_frame)))
        self.set_read_only_cells(row, "Start Frame", start_frame_item)
        
        # Set 'End Frame' Column
        end_frame_item = QTableWidgetItem(str(int(end_frame)))
        self.set_read_only_cells(row, "End Frame", end_frame_item)
    
        # Set 'Duration' Column 
        duration = int(end_frame) - int(start_frame) + 1
        duration_item = QTableWidgetItem(str(duration))
        self.set_read_only_cells(row, "Duration", duration_item)
        
        # Set 'Org Range' Column
        org_range = f"{int(start_frame)}-{int(end_frame)}\n({duration})"
        org_range_item = QTableWidgetItem(org_range)
        self.set_read_only_cells(row, "Org Range", org_range_item)
    
    def set_timecode_columns(self, row, start_frame_path, end_frame_path):
        if self.__is_edit:
            headers = self.edit_headers
        else:
            headers = self.headers
        
        # Get TimeCode
        start_tc, end_tc = self.get_timecode_metadata(start_frame_path, end_frame_path)
        
        if not start_tc or not end_tc:
            return
        
        # Set 'TimeCode In' Column
        self.set_timecode_item(row, headers.index("TimeCode In"), start_tc)
        
        # Set 'TimeCode Out' Column
        self.set_timecode_item(row, headers.index("TimeCode Out"), end_tc)
            
    def get_timecode_metadata(self, start_frame_path, end_frame_path):
        if not os.path.exists(start_frame_path) or not os.path.exists(end_frame_path):
            logger.warning(
                f"Start or End Frame Path not exists.\n Start Frame: {start_frame_path}\n End Frame: {end_frame_path}"
                )
            return None, None
        
        file_format = os.path.splitext(start_frame_path)[-1]
        if file_format == ".exr":
            start_metadata = OpenEXR.InputFile(start_frame_path).header()
            end_metadata = OpenEXR.InputFile(end_frame_path).header()
            start_timecode = start_metadata.get("timeCode", None)
            end_timecode = end_metadata.get("timeCode", None)
            
            if not start_timecode or not end_timecode:
                return None, None
            
            return start_timecode, end_timecode
        
        elif file_format == ".dpx":
            try:
                metadata = pydpx_meta.DpxHeader(start_frame_path)
                timecode = metadata.tv_header.time_code
                if timecode:
                    return timecode
            except:
                return None, None
        
        else:
            return None, None
        
    def set_timecode_item(self, row, col, timecode):
        if self.__is_edit:
            table = self.edit_table_widget
        else:
            table = self.plate_table_widget
        try:
            timecode_str = f"{timecode.hours:02d}:{timecode.minutes:02d}:{timecode.seconds:02d}:{timecode.frame:02d}" if isinstance(timecode, Imath.TimeCode) else timecode
            timecode_item = QTableWidgetItem(str(timecode_str))
            timecode_item.setFlags(timecode_item.flags() & ~Qt.ItemIsEditable)
            timecode_item.setBackgroundColor(QColor(30, 30, 30))
            table.setItem(row, col, timecode_item)
        except Exception as e:
            logger.error(traceback.format_exc())
            timecode_item = QTableWidgetItem("")
            timecode_item.setFlags(timecode_item.flags() & ~Qt.ItemIsEditable)
            timecode_item.setBackgroundColor(QColor(30, 30, 30))
            table.setItem(row, col, timecode_item)
            
    def set_thumbnail_column(self, row, thumb_path):
        if self.__is_edit:
            table = self.edit_table_widget
            headers = self.edit_headers
        else:
            table = self.plate_table_widget
            headers = self.headers
            
        if not os.path.exists(thumb_path):
            logger.warning(f"Thumbnail not found: {thumb_path}")
            return
        
        thumb_pixmap = QPixmap(thumb_path)
        if thumb_pixmap.isNull():
            logger.warning(f"Thumbnail is null: {thumb_path}")
            return
        
        thumb_lb = QLabel()
        thumb_pixmap = thumb_pixmap.scaledToWidth(table.columnWidth(headers.index("Thumbnail")))
        thumb_lb.setPixmap(thumb_pixmap)
        thumb_lb.setScaledContents(True)
        thumb_widget = QWidget()
        thumb_layout = QHBoxLayout(thumb_widget)
        thumb_layout.setAlignment(Qt.AlignCenter)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.addWidget(thumb_lb)
        table.setCellWidget(row, headers.index("Thumbnail"), thumb_widget)
        table.model().setData(table.model().index(row, headers.index("Thumbnail")), thumb_path)
    
    @disconnect_table_event
    def load_excel_file(self):
        if self.__is_edit:
            folder = self.edit_scan_folder_le.text()
            table = self.edit_table_widget
            headers = self.edit_headers
            excel_file = self.edit_excel_file_cmbx.currentText()
            read_only_table = self.headers_readonly_table.copy()
            read_only_table.append("Type")
        else:
            folder = self.scan_folder_le.text()
            table = self.plate_table_widget
            headers = self.headers
            excel_file = self.excel_file_cmbx.currentText()
            read_only_table = self.headers_readonly_table
        
        if not folder:
            QMessageBox.warning(self, "Warning", "스캔 폴더를 선택해주세요.")
            return
        
        if not excel_file or excel_file == "No Excel Files Found":
            return
        
        # Show Loading Dialog
        self.loading_dialog.show()
        QApplication.processEvents()
        
        try:
            excel_path = os.path.join(folder, excel_file).replace("/", os.sep)
            
            # Get Data Frame
            df = self.excel_manager.load_excel(self, excel_path, not self.__is_edit)
            
            # Set Table Data
            table.clearContents()
            table.setRowCount(len(df))
            table.setColumnCount(len(df.columns))
            
            for row in range(len(df)):
                for col in df.columns:
                    value = df.iloc[row][col]
                    if isinstance(value, float) and value.is_integer():
                        value = int(value)
                        
                    # Set Columns
                    if col == "Render":
                        render_widget = QWidget()
                        render_layout = QHBoxLayout(render_widget)
                        render_layout.setAlignment(Qt.AlignCenter)
                        render_layout.setContentsMargins(0, 0, 0, 0)
                        render_ckbx = QCheckBox()
                        render_ckbx.setChecked(bool(value))
                        render_ckbx.setStyleSheet("QCheckBox::indicator { margin-left: 8; margin-right: 0; }")
                        render_layout.addWidget(render_ckbx)
                        table.setCellWidget(row, headers.index("Render"), render_widget)
                    elif col == "Thumbnail":
                        self.set_thumbnail_column(row, value)
                    elif col.startswith("Start Frame -") or col == "Start Frame":
                        item = QTableWidgetItem(str(value))
                        self.set_read_only_cells(row, "Start Frame", item)
                    elif col == "Camera Model" or col == "Lens mm" or col == "Camera FPS":
                        continue
                    elif col == "Clip Name" and not self.__is_edit:
                        item = QTableWidgetItem(str(value))
                        self.set_read_only_cells(row, "Clip Name", item)
                    else:
                        item = QTableWidgetItem(str(value))
                        table.setItem(row, headers.index(col), item)
        except Exception as e:
            self.loading_dialog.hide()
            QMessageBox.critical(self, "Error", f"엑셀 파일을 불러오는 중 오류가 발생했습니다:\n{e}")
            logger.error(traceback.format_exc())
            return
        
        self.loading_dialog.hide()
            
    def create_excel_file(self):
        # Convert Current Table Data to DataFrame

        if not self.__is_edit:
            tab = "plate"
        data_root = self.scan_folder_le.text()
        row_cnt = self.plate_table_widget.rowCount()
        col_cnt = self.plate_table_widget.columnCount()
        
        if row_cnt == 0 or col_cnt == 0:
            QMessageBox.warning(self, "Warning", "데이터가 없습니다.")
            logger.warning("No data found in table.")
            return

        # Get Excel File Path
        excel_dir = data_root.replace("/", os.sep)
        excel_file = os.path.join(excel_dir, f"{os.path.basename(data_root)}_v01.xlsx")
        if os.path.exists(excel_file):
            ver = 1
            while os.path.exists(excel_file):
                ver += 1
                excel_file = os.path.join(excel_dir, f"{os.path.basename(data_root)}_v{ver:02}.xlsx").replace("/", os.sep)
        
        # Set temp header list for New start frame
        __header_list = self.headers.copy()
        __header_list.remove("Start Frame")
        
        # Insert Start Frame Header
        start_frame_header = f"Start Frame - {self.render_start_frame_spbx.value()}"
        end_frame_idx = self.headers.index("End Frame")
        __header_list.insert(end_frame_idx - 1, start_frame_header)
        
        # Get Data
        data = []
        for row in range(row_cnt):
            result = {}
            for header in __header_list:
                # Set Start Frame
                if header.startswith("Start Frame -"):
                    value = self.plate_table_widget.item(row, self.headers.index("Start Frame")).text()
                    result[header] = value
                    continue
                
                # Set Other Columns
                col = self.headers.index(header)
                if col == self.headers.index("Render"):    
                    render = self.plate_table_widget.cellWidget(row, col)
                    ckbx = render.findChild(QCheckBox)
                    value = ckbx.isChecked()
                elif col == self.headers.index("Thumbnail"):
                    value = self.plate_table_widget.model().data(self.plate_table_widget.model().index(row, col))
                else:
                    try:
                        value = self.plate_table_widget.item(row, col).text()
                    except:
                        value = ""
                result[self.headers[col]] = value
            data.append(result)
            
        try:
            excel_path = self.excel_manager.make_excel(self, data_root, row_cnt, col_cnt, excel_file, data, tab, start_frame_header)
        except Exception as e:
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"엑셀 파일을 생성하는 중 오류가 발생했습니다:\n{e}")
            return

        self.set_excel_list(data_root)
        
        return excel_path
    
    def create_edit_excel_file(self):
        if self.__is_edit:
            tab = "edit"

        data_root = self.edit_scan_folder_le.text()
        row_cnt = self.edit_table_widget.rowCount()
        col_cnt = self.edit_table_widget.columnCount()
        headers = self.edit_headers
        
        if row_cnt == 0 or col_cnt == 0:
            QMessageBox.warning(self, "Warning", "데이터가 없습니다.")
            return
        
        # Get Excel File Path
        excel_dir = data_root.replace("/", os.sep)
        excel_file = os.path.join(excel_dir, f"{os.path.basename(data_root)}_v01.xlsx")
        if os.path.exists(excel_file):
            ver = 1
            while os.path.exists(excel_file):
                ver += 1
                excel_file = os.path.join(excel_dir, f"{os.path.basename(data_root)}_v{ver:02}.xlsx").replace("/", os.sep)

        # Get Data                
        data = []
        for row in range(row_cnt):
            result = {}
            for header in headers:
                col = headers.index(header)
                if col == headers.index("Render"):
                    render = self.edit_table_widget.cellWidget(row, col)
                    ckbx = render.findChild(QCheckBox)
                    value = ckbx.isChecked()
                elif col == headers.index("Thumbnail"):
                    value = self.edit_table_widget.model().data(self.edit_table_widget.model().index(row, col))
                else:
                    try:
                        value = self.edit_table_widget.item(row, col).text()
                    except:
                        value = ""
                result[headers[col]] = value
            data.append(result)
            
        try:
            excel_path = self.excel_manager.make_excel(self, data_root, row_cnt, col_cnt, excel_file, data, tab)
        except Exception as e:
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"엑셀 파일을 생성하는 중 오류가 발생했습니다:\n{e}")
            return
        
        self.set_excel_list(data_root)
        return excel_path
    
    def toggle_edit_type(self):
        current_type = self.edit_task_cmbx.currentText()
        
        for row in range(self.edit_table_widget.rowCount()):
            type_item = QTableWidgetItem(current_type)
            self.set_read_only_cells(row, "Type", type_item)

    def table_context_menu(self, pos):
        # Table Context Menu
        self.table_menu = QMenu()
        
        # Actions
        self.open_action = self.table_menu.addAction("Open Scan Folder")
        self.table_menu.addSeparator()
        self.check_selected_action = self.table_menu.addAction("Check Selected")
        self.uncheck_selected_action = self.table_menu.addAction("Uncheck Selected")
        self.table_menu.addSeparator()
        self.check_all_action = self.table_menu.addAction("Check All")
        self.uncheck_all_action = self.table_menu.addAction("Uncheck All")
        self.table_menu.addSeparator()
        self.reload_scan_action = self.table_menu.addAction("Reload Scan Folder")
        
        action = self.table_menu.exec_(self.plate_table_widget.mapToGlobal(pos))
        if action == self.open_action:
            self.open_scan_folder()
        elif action == self.check_selected_action:
            self.set_checkbox_state(state=True)
        elif action == self.uncheck_selected_action:
            self.set_checkbox_state(state=False)
        elif action == self.check_all_action:
            self.set_checkbox_state(target="all", state=True)
        elif action == self.uncheck_all_action:
            self.set_checkbox_state(target="all", state=False)
        elif action == self.reload_scan_action:
            self.reload_scan_folder()
            
    @disconnect_table_event
    def table_item_changed(self, item):
        row, col = item.row(), item.column()
        try:
            header = self.headers[col]
        except:
            return
        handling_list = [
            "Start Frame", "Frame Handle", "First Frame Offset", "End Frame Offset", 
            "Retime End Frame", "Retime TimeCode Out", "Retime Speed"
            ]
        
        # Check if header is in handling list
        if header not in handling_list:
            return
        
        # Check if item is empty
        if not item.text():
            return
        
        # Check if item is a number
        if not header == "Retime TimeCode Out":
            try:
                float(item.text())
            except ValueError:
                self.plate_table_widget.item(row, col).setText("")
                return
        
        # Get Items
        start_frame_item = self.plate_table_widget.item(row, self.headers.index("Start Frame"))
        end_frame_item = self.plate_table_widget.item(row, self.headers.index("End Frame"))
        duration_item = self.plate_table_widget.item(row, self.headers.index("Duration"))
        frame_handle_item = self.plate_table_widget.item(row, self.headers.index("Frame Handle"))
        offset_first_item = self.plate_table_widget.item(row, self.headers.index("First Frame Offset"))
        offset_end_item = self.plate_table_widget.item(row, self.headers.index("End Frame Offset"))
        retime_end_frame_item = self.plate_table_widget.item(row, self.headers.index("Retime End Frame"))
        retime_end_tc_item = self.plate_table_widget.item(row, self.headers.index("Retime TimeCode Out"))
        retime_speed_item = self.plate_table_widget.item(row, self.headers.index("Retime Speed"))
        
        # Get Values
        start_frame = int(start_frame_item.text())
        offset_first = int(offset_first_item.text()) if offset_first_item.text() else 0
        offset_end = int(offset_end_item.text()) if offset_end_item.text() else 0
        org_range = self.plate_table_widget.item(row, self.headers.index("Org Range")).text()
        org_duration = int(org_range.split("(")[1].replace(")", ""))
        new_end_frame = int(end_frame_item.text()) if end_frame_item.text() else 0
        
        # If Start Frame Changed
        if header == "Start Frame":
            # Get Data
            start_frame = int(item.text())
            frame_handle = self.render_start_frame_spbx.value() - start_frame
            duration = int(duration_item.text()) if duration_item.text() else 1
            end_frame = start_frame + duration - 1
            
            # Set Data
            end_frame_item.setText(str(end_frame))
            frame_handle_item.setText(str(frame_handle))
            retime_end_frame = retime_end_frame_item.text()
            if retime_end_frame:
                retime_end_frame_item.setText(str(end_frame))
        
        # If Frame Handle Changed
        elif header == "Frame Handle":
            # Get Data
            start_frame = int(start_frame_item.text())
            frame_handle = int(item.text()) if item.text() else 0
            start_frame_handle = int(self.render_start_frame_spbx.value()) - frame_handle
            duration = int(duration_item.text()) if duration_item.text() else 1
            end_frame_handle = start_frame_handle + duration - 1
            
            start_frame_item.setText(str(start_frame_handle))
            end_frame_item.setText(str(end_frame_handle))
            retime_end_frame = retime_end_frame_item.text()
            if retime_end_frame:
                retime_end_frame_item.setText(str(end_frame_handle))
        
        # If First Frame Offset Changed
        elif header == "First Frame Offset":
            try:
                offset_first = int(item.text())
            except:
                offset_first = int(float(item.text())) if item.text() else 0
                offset_first_item.setText(str(offset_first))

            new_end_frame = start_frame + org_duration - 1 - offset_first - offset_end
            # Check if new end frame is valid
            if new_end_frame < start_frame or offset_first < 0:
                offset_first_item.setText("")
                new_end_frame = start_frame + org_duration - 1
            self.clear_retime_items(row)
            
        # If End Frame Offset Changed   
        elif header == "End Frame Offset":
            try:
                offset_end = int(item.text())
            except:
                offset_end = int(float(item.text())) if item.text() else 0
                offset_end_item.setText(str(offset_end))

            new_end_frame = start_frame + org_duration - 1 - offset_first - offset_end
            # Check if new end frame is valid
            if new_end_frame < start_frame or offset_end < 0:
                offset_end_item.setText("")
                new_end_frame = start_frame + org_duration - 1 - offset_first
            self.clear_retime_items(row)
            
        # If Retime End Frame Changed  
        elif header == "Retime End Frame":
            # clear retime timecode out and retime speed
            retime_end_tc_item.setText("")
            retime_speed_item.setText("")
            
            try:
                new_end_frame = int(item.text())
            except:
                new_end_frame = int(float(item.text())) if item.text() else 0
                retime_end_frame_item.setText(str(new_end_frame))

            new_duration = new_end_frame - start_frame + 1
            # Check if new duration is valid
            if new_duration < 1:
                new_end_frame = start_frame + org_duration - 1 - offset_first - offset_end
                retime_speed_item.setText("")
                retime_end_frame_item.setText("")
            else:
                retime_speed = round((org_duration - offset_first - offset_end) / new_duration, 3)
                retime_speed_item.setText(str(retime_speed))
            retime_end_tc_item.setText("")
        
        # If Retime TimeCode Out Changed  
        elif header == "Retime TimeCode Out":
            # clear retime end frame and retime speed
            retime_end_frame_item.setText("")
            retime_speed_item.setText("")
            
            new_end_frame = 0
            if not item.text():
                new_end_frame = start_frame + org_duration - 1 - offset_first - offset_end
                self.clear_retime_items(row)
                return
            
            # Check timecode is valid
            new_end_tc = item.text()
            if not re.match(r"^\d{2}:\d{2}:\d{2}:\d{2}$", new_end_tc):
                self.clear_retime_items(row)
                return
            
            # Get TimeCode
            new_end_tc = Timecode(f"{self.render_fps_spbx.value()}", f"{new_end_tc}")
            
            # Get Sequence data
            data_root = self.scan_folder_le.text().replace(os.sep, "/")
            scan_name = self.plate_table_widget.item(row, self.headers.index("Scan Data")).text() if self.plate_table_widget.item(row, self.headers.index("Scan Data")) else None
            if not scan_name:
                logger.warning("Scan Data not found.")
                QMessageBox.warning(self, "Warning", "Scan Data가 없습니다.")
                return
            
            data_path = os.path.join(data_root, scan_name)
            # if data_path is sequence root
            if os.path.isdir(data_path):
                sequence_info = self.check_image_sequence(data_path)
                if not sequence_info:
                    logger.warning(f"Sequence not found in {data_path}")
                    QMessageBox.warning(self, "Warning", "시퀀스를 찾을 수 없습니다.")
                    return

                _start_frame, _end_frame, _frame_to_path = sequence_info
                _start_frame_path, _end_frame_path = _frame_to_path[int(_start_frame)], _frame_to_path[int(_end_frame)]
                if not _start_frame or not _end_frame:
                    logger.warning(f"Sequence not found in {data_path}")
                    QMessageBox.warning(self, "Warning", "시퀀스를 찾을 수 없습니다.")
                    return
                
                filename = os.path.basename(_start_frame_path)
                seq_timecode = ""
                if filename.endswith(".dpx"):
                    _dpx = pydpx_meta.DpxHeader(_start_frame_path)
                    seq_timecode = Timecode(f"{self.render_fps_spbx.value()}", _dpx.tv_header.time_code)
                    
                elif filename.endswith(".exr"):
                    _exr = OpenEXR.InputFile(_start_frame_path)
                    _tc_obj = _exr.header().get("timeCode", None)
                    if not _tc_obj:
                        logger.warning(f"TimeCode not found in {_start_frame_path}")
                        QMessageBox.warning(self, "Warning", "TimeCode를 찾을 수 없습니다.")
                        return
                    
                    tc_str = f"{_tc_obj.hours:02d}:{_tc_obj.minutes:02d}:{_tc_obj.seconds:02d}:{_tc_obj.frame:02d}"
                    seq_timecode = Timecode(f"{self.render_fps_spbx.value()}", tc_str)
                    
                if not seq_timecode:
                    logger.warning(f"TimeCode not found in {_start_frame_path}")
                    QMessageBox.warning(self, "Warning", "TimeCode를 찾을 수 없습니다.")
                    return
                
                new_duration = new_end_tc.frames - seq_timecode.frames + 1
                if new_duration < 1:
                    new_end_frame = start_frame + org_duration - 1 - offset_first - offset_end
                    self.clear_retime_items(row)
                    return
                
                retime_speed = round((org_duration - offset_first - offset_end) / new_duration, 3)
                new_end_frame = start_frame + new_duration - 1
                
                retime_speed_item.setText(str(retime_speed))
                retime_end_frame_item.setText(str(new_end_frame))
                
            # Get Mov Data   
            else:
                valid_mov = [f for f in os.listdir(data_root) if f.startswith(scan_name) and f.endswith(".mov")]
                valid_mov.sort()
                if not valid_mov:
                    logger.warning(f"Valid mov not found in {data_root}")
                    return
                
                mov_path = os.path.join(data_root, valid_mov[0]).replace("/", os.sep)
                
                # Get Metadata
                metadata = self.ffmpeg_io.extract_mov_metadata(mov_path)
                if not metadata:
                    logger.warning(f"Metadata not found in {mov_path}")
                    return
                
                fps = metadata.get("fps", self.render_fps_spbx.value())
                start_timecode = metadata.get("start_tc", None)
                start_timecode = Timecode(fps, start_timecode)
                duration = metadata.get("duration", None)
                
                if not start_timecode or not duration:
                    logger.warning(f"TimeCode or Duration not found in {mov_path}")
                    return
                
                # Calculate new end frame
                if new_end_tc:
                    new_duration = new_end_tc.frames - start_timecode.frames + 1
                    if new_duration < 1:
                        new_end_frame = start_frame + org_duration - 1 - offset_first - offset_end
                        self.clear_retime_items(row)
                        return
                    
                    retime_speed = round((org_duration - offset_first - offset_end) / new_duration, 3)
                    new_end_frame = start_frame + new_duration - 1
                    
                    retime_speed_item.setText(str(retime_speed))
                    retime_end_frame_item.setText(str(new_end_frame))
                    
        # If Retime Speed Changed  
        elif header == "Retime Speed":
            # clear retime end frame and retime timecode out
            retime_end_frame_item.setText("")
            retime_end_tc_item.setText("")
            try:
                retime_speed = float(item.text()) if item.text() else 1
            except:
                retime_speed = 1
            
            if retime_speed > 0:
                new_end_frame = (org_duration - offset_first - offset_end + (retime_speed * start_frame) - retime_speed) / retime_speed
            else:
                new_end_frame = start_frame + org_duration - 1 - offset_first - offset_end
                
            retime_end_frame_item.setText(str(math.ceil(new_end_frame)))
            retime_end_tc_item.setText("")

        end_frame_item.setText(str(math.ceil(new_end_frame)))
        duration_item.setText(str(math.ceil(new_end_frame) - start_frame + 1))
        
    def edit_table_item_changed(self, item):
        row, col = item.row(), item.column()
        header = self.edit_headers[col]

        if not header in ["Frame Handle", "First Frame Offset", "End Frame Offset"]:
            return

        try:
            value = float(item.text())
        except ValueError:
            self.edit_table_widget.item(row, col).setText("")
            return

        # Get all items
        start_frame_item = self.edit_table_widget.item(row, self.edit_headers.index("Start Frame"))
        end_frame_item = self.edit_table_widget.item(row, self.edit_headers.index("End Frame"))
        duration_item = self.edit_table_widget.item(row, self.edit_headers.index("Duration"))
        frame_handle_item = self.edit_table_widget.item(row, self.edit_headers.index("Frame Handle"))
        org_range = self.edit_table_widget.item(row, self.edit_headers.index("Org Range")).text()
        first_frame_offset_item = self.edit_table_widget.item(row, self.edit_headers.index("First Frame Offset"))
        end_frame_offset_item = self.edit_table_widget.item(row, self.edit_headers.index("End Frame Offset"))
        
        # Parse data
        org_duration = int(org_range.split("(")[1].replace(")", ""))
        start_frame = int(org_range.split("-")[0]) 
        end_frame = int(org_range.split("-")[1].split("\n")[0])
        frame_handle = int(frame_handle_item.text()) if frame_handle_item.text() else 0
        first_frame_offset = int(first_frame_offset_item.text()) if first_frame_offset_item.text() else 0
        end_frame_offset = int(end_frame_offset_item.text()) if end_frame_offset_item.text() else 0


        if frame_handle == 0 and first_frame_offset == 0 and end_frame_offset == 0:
            print("All offsets and frame handle are 0, using original range.")
            start_frame = int(org_range.split("-")[0]) 
            end_frame = int(org_range.split("-")[1].split("\n")[0])
            start_frame_item.setText(str(start_frame))
            end_frame_item.setText(str(end_frame))

        if header == "Frame Handle":
            if value > 0 and (first_frame_offset > 0 or end_frame_offset > 0):
                QMessageBox.warning(self, "Warning", "Frame Handle을 변경하면 \nFirst Frame Offset과 End Frame Offset은 적용되지 않습니다.")
                first_frame_offset_item.setText("0")
                end_frame_offset_item.setText("0")
                return

            frame_handle = int(value)
            start_frame = 1001 - frame_handle
            end_frame = start_frame + org_duration - 1 + frame_handle * 2

        elif header in ["First Frame Offset", "End Frame Offset"]:
            if value > 0 and frame_handle > 0 :
                QMessageBox.warning(self, "Warning", f"{header}을 변경하면 \nFrame Handle은 적용되지 않습니다.")
                frame_handle_item.setText("0")
                return
            
            if header == "First Frame Offset":
                first_frame_offset = int(value)
                start_frame = start_frame + first_frame_offset
                end_frame = end_frame + end_frame_offset
                
            elif header == "End Frame Offset":
                end_frame_offset = int(value)
                start_frame = start_frame + first_frame_offset
                end_frame = end_frame + end_frame_offset

        # Update UI
        if start_frame > end_frame:
            QMessageBox.warning(self, "Warning", "Start Frame이 End Frame보다 \n클 수 없습니다.")
            item.setText("")
            return

        start_frame_item.setText(str(start_frame))
        end_frame_item.setText(str(end_frame))
        duration_item.setText(str(end_frame - start_frame + 1))
        frame_handle_item.setText(str(frame_handle))
        
    def clear_retime_items(self, row):
        self.plate_table_widget.item(row, self.headers.index("Retime Speed")).setText("")
        self.plate_table_widget.item(row, self.headers.index("Retime End Frame")).setText("")
        self.plate_table_widget.item(row, self.headers.index("Retime TimeCode Out")).setText("")

    def set_checkbox_state(self, target="selected", state=True):
        if self.__is_edit:
            table = self.edit_table_widget
            headers = self.edit_headers
        else:
            table = self.plate_table_widget
            headers = self.headers
        
        if target == "selected":
            selected = table.selectedIndexes()
            rows = {item.row() for item in selected}
        elif target == "all":
            rows = range(table.rowCount())
        else:
            return

        for row in rows:
            render = table.cellWidget(row, headers.index("Render"))
            ckbx = render.findChild(QCheckBox)
            if ckbx:
                ckbx.setChecked(bool(state))
            
    def open_scan_folder(self):
        if self.__is_edit:
            folder = self.edit_scan_folder_le.text()
        else:
            folder = self.scan_folder_le.text()
        
        if not folder:
            QMessageBox.warning(self, "Warning", "스캔 폴더를 선택해주세요.")
            return
        
        if not os.path.exists(folder):
            QMessageBox.warning(self, "Warning", "폴더가 존재하지 않습니다.")
            return
        try:
            os.startfile(folder)
        except Exception as e:
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"폴더를 열 수 없습니다:\n{e}")
        
    def open_excel_file(self):
        if self.__is_edit:
            folder = self.edit_scan_folder_le.text()
            excel_cmbx = self.edit_excel_file_cmbx
        else:
            folder = self.scan_folder_le.text()
            excel_cmbx = self.excel_file_cmbx
        
        excel_path = os.path.join(folder, excel_cmbx.currentText()).replace("/", os.sep)
        
        if not os.path.exists(excel_path):
            QMessageBox.warning(self, "Warning", "파일이 존재하지 않습니다.")
            return
        
        try:
            os.startfile(excel_path)
        except Exception as e:
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"파일을 열 수 없습니다:\n{e}")
                
    def change_view_mode(self, simple_view):
        self.__simple_view = not simple_view
        self.view_mode_btn.setIcon(self.hide_icon if self.__simple_view else self.show_icon)
        self.edit_view_mode_btn.setIcon(self.edit_hide_icon if self.__simple_view else self.edit_show_icon)
        
        # Set column visibility based on view mode
        for i in range(self.plate_table_widget.columnCount()):
            should_hide = self.__simple_view and self.headers[i] in self.headers_ignore
            self.plate_table_widget.setColumnHidden(i, should_hide)
            
        for i in range(self.edit_table_widget.columnCount()):
            should_hide = self.__simple_view and self.headers[i] in self.headers_ignore
            self.edit_table_widget.setColumnHidden(i, should_hide)
                
    def fps_changed(self):
        is_custom = self.render_fps_cmbx.currentText() == "Custom"
        self.render_fps_spbx.setEnabled(is_custom)
        
        if not is_custom:
            self.render_fps_spbx.setValue(float(self.render_fps_cmbx.currentText()))

    @disconnect_table_event
    def start_frame_changed(self, *args, **kwargs):
        start_frame = self.render_start_frame_spbx.value()
        
        for row in range(self.plate_table_widget.rowCount()):
            # Get Data
            duration = int(self.plate_table_widget.item(row, self.headers.index("Duration")).text() if self.plate_table_widget.item(row, self.headers.index("Duration")).text() else 0)
            end_frame = start_frame + duration - 1

            # Adjust for Frame Handle if present
            frame_handle = self.plate_table_widget.item(row, self.headers.index("Frame Handle")).text()
            if frame_handle:
                frame_handle = int(frame_handle)
                start_frame -= frame_handle
                end_frame -= frame_handle
                self.plate_table_widget.item(row, self.headers.index("Start Frame")).setText(str(frame_handle))

            # Update Retime End Frame if present
            retime_end_frame = self.plate_table_widget.item(row, self.headers.index("Retime End Frame")).text()
            if retime_end_frame:
                self.plate_table_widget.item(row, self.headers.index("Retime End Frame")).setText(str(end_frame))

            # Set Start and End Frame
            self.plate_table_widget.item(row, self.headers.index("Start Frame")).setText(str(start_frame))
            self.plate_table_widget.item(row, self.headers.index("End Frame")).setText(str(end_frame))

    def switch_colorspace(self):
        use_nuke_default = self.colorspace_switch_btn.text() == "Use Nuke Default"
        self.__use_nuke_colorspace = use_nuke_default
        self.colorspace_switch_btn.setText("Use OCIO Config" if use_nuke_default else "Use Nuke Default")

        # Toggle visibility based on the selected colorspace
        self.colorspace_input_cmbx.setVisible(not use_nuke_default)
        self.colorspace_output_cmbx.setVisible(not use_nuke_default)
        self.colorspace_ocio_lb.setVisible(not use_nuke_default)
        self.colorspace_ocio_le.setVisible(not use_nuke_default)
        self.colorspace_ocio_btn.setVisible(not use_nuke_default)
        
        self.colorspace_input_cmbx_nuke.setVisible(use_nuke_default)
        self.colorspace_output_cmbx_nuke.setVisible(use_nuke_default)

    def browse_ocio_config(self):
        current_ocio_path = self.colorspace_ocio_le.text()
        path = current_ocio_path if current_ocio_path else "W:/Library/Global"
        
        ocio_config = QFileDialog.getOpenFileName(self, "Select OCIO Config", path, "OCIO Config (*.ocio)")[0]
        if not ocio_config:
            return
        
        self.colorspace_ocio_le.setText(ocio_config)
        self.colorspace_input_cmbx.reload_path(ocio_config)
        self.colorspace_output_cmbx.reload_path(ocio_config)
        
    def browse_cube_dir(self):
        current_cube_path = self.colorspace_cube_le.text()
        path = current_cube_path if current_cube_path else self.default_drive
        
        cube_dir = QFileDialog.getExistingDirectory(self, "Select Cube Directory", path, ~QFileDialog.ShowDirsOnly)
        if not cube_dir:
            return
        
        self.colorspace_cube_le.setText(cube_dir)
        self.populate_cube_files()
            
    def reformat_changed(self):
        if self.render_reformat_cmbx.currentText() == "Custom":
            self.render_reformat_x_spbx.setEnabled(True)
            self.render_reformat_y_spbx.setEnabled(True)
            self.render_reformat_x_spbx.editingFinished.connect(self.set_plate_resolution)
            self.render_reformat_y_spbx.editingFinished.connect(self.set_plate_resolution)
        elif self.render_reformat_cmbx.currentText() == "Original":
            self.render_reformat_x_spbx.setEnabled(False)
            self.render_reformat_y_spbx.setEnabled(False)
            self.render_reformat_x_spbx.setValue(0)
            self.render_reformat_y_spbx.setValue(0)
            self.set_plate_resolution()
        else:
            self.render_reformat_x_spbx.setEnabled(False)
            self.render_reformat_y_spbx.setEnabled(False)
            preset = self.render_reformat_cmbx.currentText().split("_")[-1].split("x")
            self.render_reformat_x_spbx.setValue(int(preset[0]))
            self.render_reformat_y_spbx.setValue(int(preset[1]))
            self.set_plate_resolution()
    
    def crop_changed(self):
        if self.render_crop_cmbx.currentText() == "Custom":
            self.render_crop_x_spbx.setEnabled(True)
            self.render_crop_y_spbx.setEnabled(True)
        else:
            self.render_crop_x_spbx.setEnabled(False)
            self.render_crop_y_spbx.setEnabled(False)
            
    def validate_version(self):
        if self.__is_edit:
            project_name = self.edit_project_cmbx.currentText()
            table = self.edit_table_widget
            headers = self.edit_headers
        else:
            project_name = self.project_cmbx.currentText()
            table = self.plate_table_widget
            headers = self.headers
        
        # Get Selected Rows and Confirm
        selected_rows = self._get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "선택된 데이터가 없습니다.")
            return
        
        # loading dialog
        self.loading_dialog.show()
        QApplication.processEvents()
        
        err_list = []
        for row in selected_rows:
            # Get table data
            row_data = self._get_row_data(row)
            sequence = row_data.get("Sequence") if row_data.get("Sequence") else ""
            shot_name = row_data.get("Shot Name") if row_data.get("Shot Name") else ""
            _type = row_data.get("Type") if row_data.get("Type") else ""
            
            if not sequence:
                err_list.append(f"{row + 1}행에 시퀀스가 없습니다.")
                continue
            if not shot_name:
                err_list.append(f"{row + 1}행에 샷 이름이 없습니다.")
                continue
            if not _type:
                err_list.append(f"{row + 1}행에 타입이 없습니다.")
                continue
            
            # Find Version, set version column. if not found, set 1
            try:
                version_list, cube_name = sg_manager.validate_versions(project_name, sequence, shot_name, _type)
            except Exception as e:
                logger.error(traceback.format_exc())
                err_list.append(f"Error occurred while finding versions: {e}")
                self.loading_dialog.hide()
                continue
            
            # Set Latest Version
            set_version = 1
            if version_list:
                for version in version_list:
                    set_version = int(version.split("_v")[-1].split('_')[0]) + 1
            
            table.item(row, headers.index("Version")).setText(str(set_version))
            
            # Set Cube Name
            if not self.__is_edit:
                if cube_name:
                    # Get Delegate's Items List
                    items = table.itemDelegateForColumn(headers.index("Cube")).get_items()
                    
                    table.item(row, headers.index("Cube")).setText(cube_name) \
                    if cube_name in items \
                    else table.item(row, headers.index("Cube")).setText("None")
                else:
                    table.item(row, headers.index("Cube")).setText("None")
            
            self.loading_dialog.hide()
        
        if err_list:
            # process error list
            self.loading_dialog.hide()
            err_msg = "\n".join([f"{err}" for err in err_list])
            logger.error(f"Error occurred while validating version: {err_list}")
            QMessageBox.critical(self, "Error", f"버전을 찾는 중 오류가 발생했습니다:\n{err_msg}")
        
    def collect_files(self):
        print("Not Implemented")
        
    def start_plate_handler(self):
        err_list = self.process_plate()
        
        
        if err_list:
            # set messagebox error numbered
            self.processing_dialog.hide()
            if len(err_list) == 1:
                err_msg = err_list[0]
            else:
                err_msg = "\n".join([f"{i+1}. {err}" for i, err in enumerate(err_list)])
            self.status_bar_error(f"Error occurred while processing files")
            QMessageBox.critical(self, "Error", f"{err_msg}")
            logger.error(f"Error occurred while rendering files: {err_list}")
            return
        else:
            self.processing_dialog.hide()
            self.status_bar_info("Rendering job creation is complete.")
            QMessageBox.information(self, "Success", "렌더링 잡 생성이 완료되었습니다.")
            
    def start_edit_handler(self):
        err_list = self.process_edit()
        if err_list:
            self.processing_dialog.hide()
            if len(err_list) == 1:
                err_msg = err_list[0]
            else:
                err_msg = "\n".join([f"{i+1}. {err}" for i, err in enumerate(err_list)])
            self.status_bar_error(f"Error occurred while processing files")
            QMessageBox.critical(self, "Error", f"{err_msg}")
            logger.error(f"Error occurred while rendering files: {err_list}")
            return
        else:
            self.processing_dialog.hide()
            self.status_bar_info("Edit Mov arrangement is complete.") 
            QMessageBox.information(self, "Success", "편집본 배치가 완료되었습니다.")
       
    def process_edit(self):
        selected_rows = self._validate_selection()
        if not selected_rows:
            return ["선택된 데이터가 없습니다."]
        
        if not self._confirm_process():
            return ["편집본 배치를 취소했습니다."]
        
        project_name = self.edit_project_cmbx.currentText()
        sg_proj_data = sg_manager.get_project_data(project_name)
        data_root = self.edit_scan_folder_le.text().replace(os.sep, "/")
        
        self.processing_dialog.show()
        QApplication.processEvents()
        
        shot_cache = {}
        err_list = []
        
        for row in selected_rows:
            row_data = self._get_row_data(row)
            self.status_bar_debug(f"Processing {row + 1}/{len(selected_rows)}: {row_data.get('Scan Data')}")
            
            sg_shot, err_msg = self._process_shot_cache(shot_cache, sg_proj_data, row_data)
            if err_msg:
                err_list.append(err_msg)
                continue
            
            orig_mov_path = os.path.join(data_root, f"{row_data.get('Scan Data')}.mov").replace(os.sep, "/")
            dst_root = os.path.join(self.default_drive, project_name, "sequences", row_data.get("Sequence"), row_data.get("Shot Name"), self.edit_task_cmbx.currentText(), f"v{int(row_data.get('Version')):03d}").replace(os.sep, "/")
            dst_mov_name = f"{row_data.get('Shot Name')}_{row_data.get('Type')}_v{int(row_data.get('Version')):03d}_{row_data.get('Date')}.mov"
            dst_mov_path = os.path.join(dst_root, dst_mov_name).replace(os.sep, "/")
            
            try:
                edit_duration = row_data.get('Org Range').split("(")[1].replace(")", "")
            except:
                err_list.append(f"{row + 1}행의 Org Range이 올바르지 않습니다.")
                continue
            
            if not os.path.exists(orig_mov_path):
                err_list.append(f"{row + 1}행의 원본 mov 파일이 없습니다.")
                continue
            
            self.ensure_dir_exists(dst_root)
            
            # copy mov file
            try:
                shutil.copy2(orig_mov_path, dst_mov_path)
            except Exception as e:
                err_list.append(f"{row + 1}행의 mov 파일을 복사하는 중 오류가 발생했습니다: {e}")
                continue
            
            # set shot data
            sg_shot_data = {
                "sg_ep": row_data.get("Episode"),
                "sg_edit_duration": edit_duration,
                "sg_working_duration": row_data.get("Duration"),
                "sg_working_cut_in": row_data.get("Start Frame"),
                "sg_working_cut_out": row_data.get("End Frame"),
            }
            
            try:
                sg_manager.con.update("Shot", sg_shot["id"], sg_shot_data)
            except Exception as e:
                err_list.append(f"{row + 1}행의 Shot 정보를 업데이트하는 중 오류가 발생했습니다: {e}")
                continue
            
            # create task
            try:
                sg_edit_task = sg_manager.find_or_create_task(sg_proj_data, sg_shot, "EDIT", "EDIT", self.edit_task_cmbx.currentText())
            except Exception as e:
                err_list.append(f"{row + 1}행의 EDIT Task를 생성하는 중 오류가 발생했습니다: {e}")
                continue
            
            # check previous version
            v_err_list = []
            try:
                v_err_list = sg_manager.retake_low_versions(project_name, row_data.get("Shot Name"), "EDIT", self.edit_task_cmbx.currentText(), "retake")
            except Exception as e:
                err_list.append(f"{row + 1}행의 이전 버전을 체크하는 중 오류가 발생했습니다: {e}")
                continue
            
            if v_err_list:
                err_list.extend(v_err_list)
                continue
            
            # set version data
            sg_version_data = {
                "code": f"{row_data.get('Shot Name')}_{row_data.get('Type')}_v{int(row_data.get('Version')):03d}_{row_data.get('Date')}",
                "project": sg_proj_data,
                "entity": sg_shot,
                "description": row_data.get("Version Description"),
                "sg_path_to_movie": dst_mov_path,
                "sg_task": sg_edit_task,
                "user": sg_manager.get_user_by_email(self.user_data.get("email")),
                "sg_status_list": self.uploaded_version_status,
            }
            
            # create version
            try:
                sg_version = sg_manager.con.create("Version", sg_version_data)
            except Exception as e:
                err_list.append(f"{row + 1}행의 Version을 생성하는 중 오류가 발생했습니다: {e}")
                continue
            
            # update task status
            try:
                sg_manager.con.update("Task", sg_edit_task.get("id"), {"sg_status_list": "po"})
            except Exception as e:
                err_list.append(f"{row + 1}행의 EDIT Task를 업데이트하는 중 오류가 발생했습니다: {e}")
                continue
            
            # upload mov file
            try:
                sg_manager.con.upload("Version", sg_version.get("id"), dst_mov_path, "sg_uploaded_movie")
            except Exception as e:
                err_list.append(f"{row + 1}행의 mov 파일을 업로드하는 중 오류가 발생했습니다: {e}")
                continue
        return err_list
    
    def process_plate(self):
        # Get Settings
        render_settings, err_msg = self._get_settings()
        if not render_settings:
            return [err_msg]
        
        # Get Selected Rows and Confirm
        selected_rows = self._validate_selection()
        if not selected_rows:
            return ["선택된 데이터가 없습니다."]
        
        if not self._confirm_process():
            return ["렌더링을 취소했습니다."]
        
        # Set Data
        project_name = self.project_cmbx.currentText()
        sg_proj_data = sg_manager.get_project_data(project_name)
        
        data_root = self.scan_folder_le.text().replace(os.sep, "/")
        deadline_group_name = f"{project_name} IO Manager Render"
        if not sg_proj_data:
            return ["프로젝트를 찾을 수 없습니다."]
        
        if not sg_proj_data.get('sg_out_plate_ext'):
            return ["프로젝트 설정에 Out Plate Extension이 정의되지 않았습니다."]
        
        if not sg_proj_data.get('sg_default_comp_nk'):
            return ["프로젝트 설정에 default comp nk가 정의되지 않았습니다."]
        
        if not os.path.exists(sg_proj_data.get('sg_default_comp_nk')):
            return ["프로젝트 설정에 정의된 default comp nk 파일이 존재하지 않습니다."]
        
        # loading dialog
        self.processing_dialog.show()
        QApplication.processEvents()
        
        shot_cache = {}
        err_list = []
        
        scandata_pattern = re.compile(r'((.+?)(_)(\w+))(\.?)')
        digit_pattern = re.compile(r'\d+')
        
        row_cnt = 0
        for row in selected_rows:
            row_cnt += 1

            # Get table data
            row_data = self._get_row_data(row)
            scan_data = row_data.get("Scan Data")
            shot_name = row_data.get("Shot Name")
            plate_type = row_data.get("Type") # mp0
            version = f"v{int(row_data.get('Version')):03}" # v001
            plate_version = f"{plate_type}_{version}" # mp0_v001
            org_range = row_data.get("Org Range")
            start_frame = row_data.get("Start Frame")
            end_frame = row_data.get("End Frame")
            duration = row_data.get("Duration")
            start_frame_offset = row_data.get("First Frame Offset")
            end_frame_offset = row_data.get("End Frame Offset")

            self.status_bar_debug(f"Processing {row_cnt}/{len(selected_rows)}: {scan_data}")

            if int(start_frame) > int(end_frame):
                err_list.append(f"{row_cnt}행의 Start Frame이 End Frame보다 큽니다.")
                continue

            # Find or create ShotGrid shot, if already exists, use cache
            sg_shot, err_msg = self._process_shot_cache(shot_cache, sg_proj_data, row_data)
            if err_msg:
                err_list.append(err_msg)
                continue

            # Set Paths for Render
            plate_root, data_path, mov_path, connect_name = self._prepare_render_paths(project_name, data_root, row_data)
            if os.path.isfile(mov_path):

                connect_dir = os.path.join(data_root, "_io", scan_data, connect_name)
                seq_ext = sg_proj_data.get('sg_out_plate_ext')
                di_data_seq = mov_path.replace(os.sep, "/")
            else:
                connect_dir = os.path.join(data_path, connect_name).replace(os.sep, "/")
            
            self.ensure_dir_exists(connect_dir)
            
            shot_plate_dir = os.path.join(plate_root, plate_version, connect_name).replace(os.sep, "/")
            if render_settings.get("render_exr"):
                self.ensure_dir_exists(shot_plate_dir)
            
            # find mp or sp in scan data
            match = scandata_pattern.match(scan_data)
            
            if match:
                __data_name = match.group(4)
                __data_path = os.path.join(data_root, match.group(1)).replace("/", os.sep)
            else:
                __data_name = scan_data
                __data_path = data_path.replace("/", os.sep)
            
            seq_info = self.check_image_sequence(__data_path)
            
            # Set Plate Match Dict
            plate_match_dict = {}
            
            if seq_info:
                __start_frame, __end_frame, __frame_to_path = seq_info
                frame_paths_list = [__frame_to_path[f] for f in range(int(__start_frame), int(__end_frame) + 1)]
                __start_frame_path, __end_frame_path = frame_paths_list[0], frame_paths_list[-1]
                
                real_path_start_frame = digit_pattern.findall(__start_frame_path)[-1]   # ex) test_test001_v001.1001.exr -> 1001
                seq_header = os.path.basename(__start_frame_path).split(".")[0]         # ex) test_test001_v001.1001.exr -> test_test001_v001
                seq_ext = os.path.splitext(__start_frame_path)[-1]                      # ex) test_test001_v001.1001.exr -> .exr
                
                di_data_seq = os.path.join(
                    data_path, 
                    f"{seq_header}.%0{len(real_path_start_frame)}d{seq_ext} {__start_frame}-{__end_frame}"  # ex) test_test001_v001.%04d.exr 1001-1100
                    ).replace(os.sep, "/")
                
                # If render exr, adjust frame range
                if render_settings.get("render_exr"):
                    frame = int(start_frame) if start_frame else 0
                    if start_frame_offset:
                        frame -= int(start_frame_offset) if start_frame_offset else 0
                    _org_duration = int(org_range.split("(")[1].replace(")", "")) if org_range else 0
                    _end_frame = int(start_frame or 0) + _org_duration - int(start_frame_offset or 0) - int(end_frame_offset or 0) - 1

                    # Set Plate Match Dict
                    for frame_path in frame_paths_list:
                        di_data_path = frame_path.replace(os.sep, "/")
                        shot_data_path = os.path.join(shot_plate_dir, f"{connect_name}.{frame:04}{seq_ext}")
                        plate_match_dict[di_data_path] = shot_data_path
                        frame += 1
            
            # Set Deadline Dependency List
            upload_depen_list = []
            
            # Set EXR Path
            plate_job_list = []
            shot_plate_path = ""
            if render_settings.get("render_exr"):
                shot_data_path = os.path.join(shot_plate_dir, f"{connect_name}.%04d{seq_ext if seq_ext.startswith('.') else '.' + seq_ext}").replace(os.sep, "/")
                # If no need to Nuke Process, copy plate to shot data
                if (os.path.splitext(di_data_seq)[-1].lower() == ".mov" or 
                    render_settings["reformat_x"] or 
                    render_settings["reformat_y"] or 
                    not render_settings["crop_preset"] == "Original"  or
                    org_range.split("(")[1].replace(")", "") != duration):
                    
                    shot_plate_path = shot_data_path.replace(os.sep, "/")
                else:
                    copy_py_path = os.path.join(connect_dir, f".copy_to_{connect_name}.py")
                    try:
                        plate_job_list = self.deadline_manager.submit_copy_job(
                            plate_match_dict, copy_py_path, priority=int(render_settings["priority"]), 
                            depen_list=[], grp_name=deadline_group_name
                        )
                        upload_depen_list += plate_job_list
                    except Exception as e:
                        logger.error(traceback.format_exc())
                        err_list.append(f"Error occurred while submitting copy job: {e}")
                        continue
                
            # Set JPG Path
            shot_jpg_path = ""
            if render_settings.get("render_jpg"):
                shot_jpg_dir = os.path.join(plate_root, plate_version, "jpg", connect_name)
                self.ensure_dir_exists(shot_jpg_dir)
                shot_jpg_path = os.path.join(shot_jpg_dir, f"{connect_name}.%04d.jpg").replace(os.sep, "/")
                
            # Set MOV Path
            shot_mov_path = ""
            _export_mov = False
            if render_settings.get("render_mov"):
                shot_mov_dir = os.path.join(plate_root, plate_version).replace(os.sep, "/")
                shot_mov_path = os.path.join(shot_mov_dir, f"{connect_name}.mov").replace(os.sep, "/")
                self.ensure_dir_exists(shot_mov_dir)
                _export_mov = True
                
            # Set PNG Path
            shot_png_path = ""
            if render_settings.get("render_png"):
                shot_png_dir = os.path.join(plate_root, plate_version, "png", connect_name)
                self.ensure_dir_exists(shot_png_dir)
                shot_png_path = os.path.join(shot_png_dir, f"{connect_name}.%04d.png").replace(os.sep, "/")
            
            create_comp = False
            sg_plate_task = None

            # Set SG Task
            mp_plate = plate_type.lower().startswith("mp")
            sp_plate = plate_type.lower().startswith("sp")
            if plate_type.lower() == "edit":
                try:
                    sg_plate_task = sg_manager.find_or_create_task(sg_proj_data, sg_shot, "EDIT", "EDIT", "edit")
                except Exception as e:
                    logger.error(traceback.format_exc())
                    err_list.append(f"Error occurred while finding or creating ShotGrid task: {e}")
                    continue

            elif mp_plate or sp_plate:
                try:
                    sg_plate_task = sg_manager.find_or_create_task(sg_proj_data, sg_shot, "Plate", "Plate", "plate")
                except Exception as e:
                    logger.error(traceback.format_exc())
                    err_list.append(f"Error occurred while finding or creating ShotGrid task: {e}")
                    continue
                
                # If data type is main plate, make comp script
                if mp_plate:
                    try:
                        # Create CMP Task
                        sg_manager.find_or_create_task(sg_proj_data, sg_shot, "Comp", "CMP", "cmp")
                    except Exception as e:
                        logger.error(traceback.format_exc())
                        err_list.append(f"Error occurred while finding or creating ShotGrid task: {e}")
                        continue
                    
                    shot_root = os.path.join(self.default_drive, project_name, "sequences", row_data.get("Sequence"), shot_name, "CMP", "cmp").replace(os.sep, "/")
                    nk_file = f'{shot_name}_cmp_v000.nk'

                    exr_output_dir = os.path.join(shot_root, "wip", "nuke", "images").replace(os.sep, "/")
                    exr_output_name = f"{shot_name}_cmp_{version}.%04d.exr"
                    mov_output_dir = os.path.join(shot_root, "wip", "review").replace(os.sep, "/")
                    mov_output_name = f"{shot_name}_cmp_{version}.mov"
                    exr_output_path = os.path.join(exr_output_dir, exr_output_name).replace(os.sep, "/")
                    mov_output_path = os.path.join(mov_output_dir, mov_output_name).replace(os.sep, "/")
                    
                    nuke_shot_work_path = os.path.join(shot_root, "wip", "nuke", "scenes", nk_file)
                    self.ensure_dir_exists(os.path.dirname(nuke_shot_work_path))
                    
                    comp_temp_py = nuke_shot_work_path.replace(".nk", ".py").replace(os.sep, "/")
                    nk_plate_path = ""
                    if render_settings.get("render_exr"):
                        nk_plate_path = shot_data_path
                    elif not os.path.exists(nuke_shot_work_path) and render_settings.get("render_mov"):
                        nk_plate_path = shot_mov_path
                    elif not os.path.exists(nuke_shot_work_path) and render_settings.get("render_jpg"):
                        nk_plate_path = shot_jpg_path
                    elif not os.path.exists(nuke_shot_work_path) and render_settings.get("render_png"):
                        nk_plate_path = shot_png_path
                        
                    if nk_plate_path and not os.path.exists(comp_temp_py):
                        cube_path = ""
                        cube_dir = self.colorspace_cube_le.text().replace("/", os.sep)
                        cube_name = self.plate_table_widget.item(row, self.headers.index("Cube")).text()
                        if cube_name and not cube_name == "None":
                            cube_path = os.path.join(cube_dir, cube_name).replace(os.sep, "/")
                            if not os.path.exists(cube_path):
                                cube_path = ""
                        _paths = (nuke_shot_work_path, nk_plate_path, sg_proj_data.get("sg_default_comp_nk").replace(os.sep, "/"), exr_output_path, mov_output_path, cube_path)
                        try:
                            nk_cmd = nuke_manager.get_comp_cmd(_paths, row_data, render_settings, sg_proj_data, comp_temp_py)
                            with open(comp_temp_py, "w", encoding="utf-8") as f:
                                f.write(nk_cmd)
                                create_comp = True
                        except Exception as e:
                            logger.error(traceback.format_exc())
                            err_list.append(f"Error occurred while creating comp script: {e}")
                            continue

                    timecode_in = row_data.get("TimeCode In")
                    timecode_out = row_data.get("TimeCode Out")

                    # Update Shot Data
                    sg_data = {
                        'sg_cut_in': int(start_frame) if start_frame else None,
                        'sg_cut_out': int(end_frame) if end_frame else None,
                        'sg_cut_duration': int(duration) if duration else None,
                        'sg_tc_in': timecode_in if timecode_in else None,
                        'sg_tc_out': timecode_out if timecode_out else None,
                    }
                    try:
                        sg_manager.con.update("Shot", sg_shot.get("id"), sg_data)
                    except Exception as e:
                        logger.error(traceback.format_exc())
                        err_list.append(f"Error occurred while updating ShotGrid data: {e}")
                        continue

            clip_name = self._prepare_clip_name(project_name, sg_shot, row_data)
            scan_path = self._prepare_scan_path(project_name, sg_shot, row_data)
            plate_resolution = self._prepare_plate_resolution(project_name, sg_shot, row_data)

            sg_data = {
                'sg_clip_name': clip_name if clip_name else None,
                'sg_scan_path': scan_path if scan_path else None,
                'sg_plate_resolution': plate_resolution if plate_resolution else None,
            }

            try:
                sg_manager.con.update("Shot", sg_shot.get("id"), sg_data)
            except Exception as e:
                logger.error(traceback.format_exc())
                err_list.append(f"Error occurred while updating ShotGrid data: {e}")
                continue

            
            try:
                sg_manager.retake_low_versions(project_name, shot_name, "plate", plate_type, "retake")
            except Exception as e:
                logger.error(traceback.format_exc())
                
            try:
                err_msg = sg_manager.get_plate_versions(sg_shot, shot_name, plate_version)
                if err_msg:
                    print("sg_manager.get_plate_versions() error")
                    err_list.append(err_msg)
            except Exception as e:
                logger.error(traceback.format_exc())
            
            # Make .nk File to Render jpg, mov
            render_nk_path = os.path.join(connect_dir, f".render_{connect_name}.nk").replace(os.sep, "/")
                    
            cube_path = ""
            cube_dir = self.colorspace_cube_le.text().replace("/", os.sep)
            cube_name = self.plate_table_widget.item(row, self.headers.index("Cube")).text()
            if cube_name and not cube_name == "None":
                cube_path = os.path.join(cube_dir, cube_name).replace(os.sep, "/")
                if not os.path.exists(cube_path):
                    cube_path = ""
            _paths = (render_nk_path, di_data_seq, shot_plate_path, shot_png_path, shot_jpg_path, shot_mov_path, cube_path)
            try:
                render_cmd = nuke_manager.get_render_cmd(_paths, row_data, render_settings, sg_proj_data)
                render_temp_py = render_nk_path.replace(".nk", ".py")
                with open(render_temp_py, "w", encoding="utf-8") as f:
                    f.write(render_cmd)
            except Exception as e:
                logger.error(traceback.format_exc())
                err_list.append(f"Error occurred while creating render script: {e}")
                continue
            
            # Submit Create nk Job
            _job_name = f"[{connect_name}] - Make Render NK"
            try:
                render_nk_id = self.deadline_manager.submit_nuke_py_to_deadline(
                    render_temp_py, 
                    _job_name, 
                    int(render_settings.get("priority")), 
                    depen_list=[], 
                    grp_name=deadline_group_name
                    )
            except Exception as e:
                logger.error(traceback.format_exc())
                err_list.append(f"Error occurred while submitting nuke job: {e}")
                continue
            
            # Submit Render Job
            plate_job_list = []
            jpg_job_list = []
            mov_job = None
            png_job_list = []
            try:
                plate_job_list, jpg_job_list, mov_job, png_job_list = self.deadline_manager.submit_nuke_to_deadline(
                    render_nk_path, row_data, render_settings, [render_nk_id], deadline_group_name, 
                    export_plate=shot_plate_path!="", 
                    export_jpg=render_settings.get("render_jpg"), 
                    export_mov=_export_mov, 
                    export_png=render_settings.get("render_png"),
                )
            except Exception as e:
                logger.error(traceback.format_exc())
                err_list.append(f"Error occurred while submitting render job: {e}")
                continue
            if plate_job_list:
                upload_depen_list += plate_job_list
            if jpg_job_list:
                upload_depen_list += jpg_job_list
            if mov_job:
                upload_depen_list.append(mov_job)
            if png_job_list:
                upload_depen_list += png_job_list
            
            if create_comp:
                _job_name = f"[{connect_name}] - Make Comp NK"
                try:
                    self.deadline_manager.submit_nuke_py_to_deadline(
                        comp_temp_py, _job_name, int(render_settings.get("priority")),
                        plate_job_list, deadline_group_name
                    )
                except Exception as e:
                    logger.error(traceback.format_exc())
                    err_list.append(f"Error occurred while submitting comp job: {e}")
                    continue
            else:
                logger.debug("No Comp Script Created")
                
            # Update Shot Data
            version_data = {
                'entity': sg_shot,
                'sg_user': sg_manager.get_user_by_email(self.user_data.get("email")),
                'name': connect_name,
                'des': row_data.get("Version Description") if row_data.get("Version Description") else "",
                'status': self.uploaded_version_status
            }
            if sg_plate_task:
                version_data['entity'] = sg_plate_task
            if render_settings.get("render_exr"):
                _input_file = shot_data_path
            elif render_settings.get("render_jpg"):
                _input_file = shot_jpg_path
            else:
                _input_file = shot_mov_path
            
            try:
                self.deadline_manager.submit_sg_upload_to_deadline(
                    version_data, _input_file, shot_mov_path, 
                    row_data, render_settings, project_name, upload_depen_list, deadline_group_name,
                    not render_settings.get("render_mov")
                )
            except Exception as e:
                logger.error(traceback.format_exc())
                err_list.append(f"Error occurred while submitting upload job: {e}")
                continue
            
        return err_list
    
    def _prepare_clip_name(self, project_name, sg_shot, row_data):
        sg_new_clip_name = self._prepare_sg_field(
            project_name, sg_shot, row_data, "Clip Name", "sg_clip_name"
        )
        return sg_new_clip_name

    def _prepare_scan_path(self, project_name, sg_shot, row_data):
        scan_folder_dir = self.scan_folder_le.text()
        sg_new_scan_path = self._prepare_sg_field(
            project_name, sg_shot, row_data, "Scan Data", "sg_scan_path", 
            extra_path=scan_folder_dir
        )
        return sg_new_scan_path

    def _prepare_plate_resolution(self, project_name, sg_shot, row_data):
        sg_new_plate_resolution = self._prepare_sg_field(
            project_name, sg_shot, row_data, 
            "Plate Resolution", "sg_plate_resolution"
        )
        return sg_new_plate_resolution

    def _prepare_sg_field(
            self, project_name, sg_shot, row_data, 
            row_key, sg_key, extra_path=None
    ):
        if not row_data:
            return

        shot_info = sg_manager.get_shot_info(project_name, sg_shot)
        sg_value = shot_info.get(sg_key)

        type_name = row_data.get("Type")
        version = row_data.get("Version")
        base_value = row_data.get(row_key)
        plate_version = f"{type_name}_v{int(version):03}"

        if extra_path:
            scan_path = os.path.join(extra_path, base_value)
            new_value = f"{plate_version} : {scan_path.replace(os.sep, '/')}"
        else:
            new_value = f"{plate_version} : {base_value}"

        return f"{sg_value}\n{new_value}" if sg_value else new_value
    
    def _process_shot_cache(self, shot_cache, sg_proj_data, row_data):
        key = (row_data["Sequence"], row_data["Shot Name"])
        if key not in shot_cache:
            try:
                sg_shot = sg_manager.find_or_create_shot(sg_proj_data, row_data["Sequence"], row_data["Shot Name"])
                shot_cache[key] = sg_shot
            except Exception as e:
                logger.error(traceback.format_exc())
                return None, f"샷그리드의 샷 정보를 생성하는 중 오류가 발생했습니다: {e}"
        return shot_cache[key], None
    
    def _prepare_render_paths(self, project_name, data_root, row_data):
        plate_root = os.path.join(self.default_drive, project_name, "sequences", row_data["Sequence"], row_data["Shot Name"], "plate")
        self.ensure_dir_exists(plate_root)
        
        connect_name = f"{row_data['Shot Name']}_{row_data['Type']}_v{int(row_data['Version']):03}"
        data_path = os.path.join(data_root, row_data["Scan Data"])
        valid_mov = [f for f in os.listdir(data_root) if f.startswith(row_data["Scan Data"]) and f.lower().endswith(".mov")]
        mov_path = os.path.join(data_root, valid_mov[0]) if valid_mov else ""
        return (plate_root, data_path, mov_path, connect_name)

    def _confirm_process(self):
        if self.__is_edit:
            ask_msg = "편집본 배치를 진행하시겠습니까?"
        else:
            ask_msg = "렌더링을 진행하시겠습니까?"
        
        if QMessageBox.question(
            self, "Confirm", ask_msg, QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.No:
            return False
        return True
    
    def _get_settings(self):
        # Get Render Settings
        data = {}
        render_exr = bool(self.render_export_exr.isChecked())
        render_mov = bool(self.render_export_mov.isChecked())
        render_jpg = bool(self.render_export_jpg.isChecked())
        render_png = bool(self.render_export_png.isChecked())
        
        if not any([render_exr, render_mov, render_jpg, render_png]):
            return {}, "최소 하나의 렌더링 옵션을 선택해주세요."

        fps = round(self.render_fps_spbx.value(), 3)

        if fps == 0:
            return {}, "FPS 값을 입력해주세요."
        
        codec = self.render_codec_cmbx.currentText()
        start_frame = round(self.render_start_frame_spbx.value())
        priority = round(self.render_priority_spbx.value())

        # Get Colorspace Settings
        ocio_config = self.colorspace_ocio_le.text()
        if not os.path.exists(ocio_config):
            return {}, "OCIO Config 파일이 존재하지 않습니다."
        
        if self.__use_nuke_colorspace:
            input_colorspace = self.colorspace_input_cmbx_nuke.currentText()
            output_colorspace = self.colorspace_output_cmbx_nuke.currentText()
        else:
            input_colorspace = self.colorspace_input_cmbx.text()
            output_colorspace = self.colorspace_output_cmbx.text()
            
        if input_colorspace == "Select Colorspace":
            return {}, "Input Colorspace를 선택해주세요."
        
        if output_colorspace == "Select Colorspace":
            return {}, "Output Colorspace를 선택해주세요."
        
        # Get Reformat Settings
        reformat_preset = ""
        reformat_x = 0
        reformat_y = 0
        
        reformat_preset = self.render_reformat_cmbx.currentText()
        reformat_x = round(self.render_reformat_x_spbx.value())
        reformat_y = round(self.render_reformat_y_spbx.value())
        
        # Get Crop Settings
        crop_preset = ""
        crop_x = 0
        crop_y = 0
        
        if self.render_crop_cmbx.currentText() == "Custom":
            crop_preset = "Custom"
            crop_x = round(self.render_crop_x_spbx.value())
            crop_y = round(self.render_crop_y_spbx.value())
        else:
            crop_preset = self.render_crop_cmbx.currentText()
        
        # Get Aspect Fit Settings
        aspect_mode = ""
        aspect_mode = self.render_aspect_fit_cmbx.currentText()
        
        # Resize Target Settings
        resize_target = ''
        if self.resize_target_all_cb.isChecked():
            resize_target = "all"
        else:
            resize_target = "mov"
                
        # append data
        data["render_exr"] = render_exr
        data["render_mov"] = render_mov
        data["render_jpg"] = render_jpg
        data["render_png"] = render_png
        data["fps"] = fps
        data["codec"] = codec
        data["start_frame"] = start_frame
        data["priority"] = priority
        data["use_ocio_colorspace"] = not self.__use_nuke_colorspace
        data["ocio_config"] = ocio_config
        data["input_colorspace"] = input_colorspace
        data["output_colorspace"] = output_colorspace
        data['reformat_preset'] = reformat_preset
        data["reformat_x"] = reformat_x
        data["reformat_y"] = reformat_y
        data["crop_preset"] = crop_preset
        data["crop_x"] = crop_x
        data["crop_y"] = crop_y
        data["aspect_mode"] = aspect_mode
        data["resize_target"] = resize_target
        
        return data, ""
    
    def _get_row_data(self, row):
        if self.__is_edit:
            table = self.edit_table_widget
            headers = self.edit_headers
        else:
            table = self.plate_table_widget
            headers = self.headers
        
        row_data = {
            header: (
                table.item(row, headers.index(header)).text() 
                if table.item(row, headers.index(header)) else ""
                )
            for header in headers
            }
        return row_data
    
    def _get_selected_rows(self):
        if self.__is_edit:
            table = self.edit_table_widget
            headers = self.edit_headers
        else:
            table = self.plate_table_widget
            headers = self.headers
        
        selected_rows = []
        for row in range(table.rowCount()):
            render = table.cellWidget(row, headers.index("Render"))
            ckbx = render.findChild(QCheckBox)
            if ckbx.isChecked():
                selected_rows.append(row)
        
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "선택된 데이터가 없습니다.")
            return None        
        
        return selected_rows
    
    def _validate_selection(self):
        selected_rows = self._get_selected_rows()
        if not selected_rows or not self._validate_row_data(selected_rows):
            return None
        return selected_rows
    
    def _validate_row_data(self, selected_rows):
        if self.__is_edit:
            table = self.edit_table_widget
            headers = self.edit_headers
        else:
            table = self.plate_table_widget
            headers = self.headers
        
        for row in selected_rows:
            sequence_item = table.item(row, headers.index("Sequence"))
            shot_name_item = table.item(row, headers.index("Shot Name"))
            scan_data_item = table.item(row, headers.index("Scan Data"))
            version_item = table.item(row, headers.index("Version"))
            org_range_item = table.item(row, headers.index("Org Range"))
            start_frame_item = table.item(row, headers.index("Start Frame"))
            end_frame_item = table.item(row, headers.index("End Frame"))
            duration_item = table.item(row, headers.index("Duration"))
            
            sequence_item = sequence_item.text() if sequence_item else ""
            shot_name_item = shot_name_item.text() if shot_name_item else ""
            scan_data_item = scan_data_item.text() if scan_data_item else ""
            version_item = version_item.text() if version_item else ""
            org_range_item = org_range_item.text() if org_range_item else ""
            start_frame_item = start_frame_item.text() if start_frame_item else ""
            end_frame_item = end_frame_item.text() if end_frame_item else ""
            duration_item = duration_item.text() if duration_item else ""

            if not sequence_item:
                QMessageBox.warning(self, "Warning", f"{scan_data_item}: Sequence 값이 없습니다.")
                return False
            if not shot_name_item:
                QMessageBox.warning(self, "Warning", f"{scan_data_item}: Shot Name 값이 없습니다.")
                return False
            if not version_item:
                QMessageBox.warning(self, "Warning", f"{scan_data_item}: Version 값이 없습니다.")
                return False 

            if self.__is_edit:
                date_item = table.item(row, headers.index("Date")).text()
                if not date_item:
                    QMessageBox.warning(self, "Warning", f"{scan_data_item}: Date 값이 없습니다.")
                    return False
                if not org_range_item:
                    QMessageBox.warning(self, "Warning", f"{scan_data_item}: Org Range 값이 없습니다.")
                    return False
                if not start_frame_item:
                    QMessageBox.warning(self, "Warning", f"{scan_data_item}: Start Frame 값이 없습니다.")
                    return False
                if not end_frame_item:
                    QMessageBox.warning(self, "Warning", f"{scan_data_item}: End Frame 값이 없습니다.")
                    return False
                if not duration_item:
                    QMessageBox.warning(self, "Warning", f"{scan_data_item}: Duration 값이 없습니다.")
                    return False
        return True
                     
    def logout(self):
        confirm = QMessageBox.question(self, "Logout", "로그아웃 하시겠습니까?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if confirm == QMessageBox.No:
            return
        
        settings = QSettings("MTHD", "IOManager")
        settings.remove("user_email")
        
        # restart app
        QApplication.quit()
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    def open_log_file(self):
        log_file = self.log_path
        if not os.path.exists(log_file):
            QMessageBox.warning(self, "Warning", "로그 파일이 존재하지 않습니다.")
            return
        
        try:
            os.startfile(log_file)
        except Exception as e:
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"로그 파일을 열 수 없습니다:\n{e}")
            return
        
    def clear_log_file(self):
        log_file = self.log_path
        if not os.path.exists(log_file):
            QMessageBox.warning(self, "Warning", "로그 파일이 존재하지 않습니다.")
            return
        
        try:
            with open(log_file, "w") as f:
                f.write("")
            QMessageBox.information(self, "Information", "로그 파일이 삭제되었습니다.")
        except Exception as e:
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"로그 파일을 지울 수 없습니다:\n{e}")
            return
        
    def closeEvent(self, event):
        self.save_settings()
        event.accept()
        
    def save_settings(self):
        settings = QSettings("MTHD", "IOManager")
        settings.setValue("project", self.project_cmbx.currentText())
        settings.setValue("edit_project", self.edit_project_cmbx.currentText())
        
        # Save User Email
        user_email = self.user_menu.title()
        user_data = sg_manager.get_user_by_email(user_email)
        if not user_data:
            return
        
        settings.setValue("user_email", self.user_menu.title())
        
    def load_settings(self):
        settings = QSettings("MTHD", "IOManager")
        
        # Load Project and Edit Project
        project = settings.value("project")
        if not project:
            return
        
        cmbx_items = [self.project_cmbx.itemText(i) for i in range(self.project_cmbx.count())]
        if project in cmbx_items:
            self.project_cmbx.setCurrentText(project)
            
        edit_project = settings.value("edit_project")
        if not edit_project:
            return
        
        cmbx_items = [self.edit_project_cmbx.itemText(i) for i in range(self.edit_project_cmbx.count())]
        if edit_project in cmbx_items:
            self.edit_project_cmbx.setCurrentText(edit_project)
            
    def ensure_dir_exists(self, path):
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
            
    def status_bar_error(self, message):
        self.status_bar.showMessage(message)
        self.status_bar.setStyleSheet("background-color: red; color: white;")
        QApplication.processEvents()
        
    def status_bar_debug(self, message):
        self.status_bar.showMessage(message)
        self.status_bar.setStyleSheet("background-color: transparent; color: white;")
        QApplication.processEvents()

    def status_bar_info(self, message):
        self.status_bar.showMessage(message)
        self.status_bar.setStyleSheet("background-color: green; color: white;")
        QApplication.processEvents()
            
            
class CustomDelegate(QStyledItemDelegate):
    def __init__(self, parent, items, default_text="None"):
        super(CustomDelegate, self).__init__(parent)
        self.items = items
        self.items.insert(0, default_text)
        self.default_text = default_text
        
    def get_items(self):
        return self.items

    def createEditor(self, parent, option, index):
        combo_box = QComboBox(parent)

        data = index.model().data(index, Qt.UserRole)
        if isinstance(data, list):
            combo_box.setStyleSheet("background-color: transparent; color: white;")
            combo_box.addItems(data)
            return combo_box

        combo_box.setStyleSheet("background-color: transparent; color: white;")
        combo_box.addItems(self.items)

        return combo_box

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value and value in self.items:
            editor.setCurrentText(value)
        else:
            editor.setCurrentText(self.default_text)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.EditRole)

class WorkerSignals(QObject):
    succeeded = Signal(int, str)
    error_occurred = Signal(int, str)
    
class ThumbnailWorker(QRunnable):
    def __init__(self, row, input_path, output_path, ffmpeg_io):
        super().__init__()
        self.row = row
        self.input_path = input_path
        self.output_path = output_path
        self.ffmpeg_io = ffmpeg_io
        self.signals = WorkerSignals()

    def run(self):
        try:
            thumb_path = self.ffmpeg_io.extract_thumbnail(self.input_path, self.output_path)
            self.signals.succeeded.emit(self.row, thumb_path)
        except Exception as e:
            self.signals.error_occurred.emit(self.row, self.input_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IOManager()
    window.show()
    sys.exit(app.exec_())