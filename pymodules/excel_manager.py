# -*- coding: utf-8 -*-

import os
import sys

import pandas as pd
import openpyxl
import xlwings as xw
from PySide2.QtWidgets import QMessageBox

# Custom Modules
try:
    import constants
    from init_logger import IOManagerLogger
except:
    from pymodules import constants
    from pymodules.init_logger import IOManagerLogger

# Set Logger
logger = IOManagerLogger(os.path.basename(__file__), constants.LOG_PATH)


class ExcelManager():
    def __init__(self):
        self.headers = constants.HEADERS
        self.headers_readonly = constants.READONLY_HEADERS
        
    def make_excel(self, parent, data_root, row_cnt, col_cnt, output_path, data, tab_name, start_frame_header_name="Start Frame"):

        # validate data
        validate_result = self.validate_data(parent, data_root, row_cnt, col_cnt, output_path, data)
        if validate_result == False:
            return
        
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            df = pd.DataFrame(data)

            df = self.set_frame_calculation_mode(tab_name, df, start_frame_header_name)

            df.to_excel(
                writer, sheet_name='Sheet1', columns=None, header=True, index=False, startrow=0, startcol=0
                )
            
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']
            
            # Set Default Format
            fmt = workbook.add_format()
            fmt.set_align('left')
            fmt.set_align('bottom')
            
            # Set ReadOnly Format
            gray_fmt = workbook.add_format({'bg_color': '#D3D3D3'})
            gray_fmt.set_align('left')
            gray_fmt.set_align('bottom')
            
            # Set Thumbnail
            thumbnail_col_index = self.headers.index("Thumbnail")
            for row, thum in enumerate(df['Thumbnail'], start=1):
                if thum:  # Ensure thumbnail path exists
                    worksheet.insert_image(row, thumbnail_col_index, thum, {'x_scale': 1, 'y_scale': 1})
            
            # Set Column
            for i, col in enumerate(df.columns):
                # Set Column Width
                if col in [start_frame_header_name, "End Frame", "Duration", "Retime End Frame"]:
                    column_len = 18
                elif col == "Thumbnail":
                    column_len = 33.5
                else:
                    column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
                    
                # Set Header Format
                ## Set Start Frame Header ReadOnly
                self.headers_readonly.append(start_frame_header_name)
                
                if col in self.headers_readonly:
                    worksheet.write(0, i, col, gray_fmt)
                    worksheet.set_column(i, i, column_len, gray_fmt)
                else:
                    worksheet.set_column(i, i, column_len, fmt)
            
            # Set Row
            for row in range(len(df.index) + 1):
                if row == 0:
                    continue
                worksheet.set_row(row, 113)      
            
        QMessageBox.information(parent, "Excel Export", f"엑셀 파일이 생성되었습니다.\n{output_path}")
        
        return output_path
    
    def set_frame_calculation_mode(self, tab_name, df, start_frame_header_name):

        start_frame_col = df.columns.get_loc(start_frame_header_name) + 1
        handle_col = df.columns.get_loc("Frame Handle") + 1
        duration_col = df.columns.get_loc("Duration") + 1
        first_offset_col = df.columns.get_loc("First Frame Offset") + 1
        end_offset_col = df.columns.get_loc("End Frame Offset") + 1
        org_range_col = df.columns.get_loc("Org Range") + 1

        if tab_name == "edit":
            # original frame range
            org_range = f'INDIRECT("RC{org_range_col}", FALSE)'
            org_start_frame = f'LEFT({org_range}, FIND("-", {org_range}) - 1)'
            org_end_frame = f'MID({org_range}, FIND("-", {org_range}) + 1, FIND("(", {org_range}) - FIND("-", {org_range}) -2)'
            org_duration = f'MID({org_range}, FIND("(", {org_range}) + 1, FIND(")", {org_range}) - FIND("(", {org_range}) - 1)'

            frame_handle = f'INDIRECT("RC{handle_col}", FALSE)'
            first_offset = f'INDIRECT("RC{first_offset_col}", FALSE)'
            end_offset = f'INDIRECT("RC{end_offset_col}", FALSE)'

            # start frame
            handle_start_frame = f'{org_start_frame} - {frame_handle}'
            first_offset_start_frame = f'{org_start_frame} + {first_offset}'
            df[start_frame_header_name] = (
                f'=IF(AND({frame_handle}<>"", {frame_handle}<>0), {handle_start_frame}, ' 
                f'IF(AND({first_offset}<>"", {first_offset}<>0), {first_offset_start_frame}, '
                f'{org_start_frame}))'
            )

            # end frame
            handle_end_frame = f'{org_end_frame} + {frame_handle}'
            end_offset_end_frame = f'{org_end_frame} + {end_offset}'
            df["End Frame"] = (
                f'=IF(AND({frame_handle}<>"", {frame_handle}<>0), {handle_end_frame}, ' 
                f'IF(AND({end_offset}<>"", {end_offset}<>0), {end_offset_end_frame}, '
                f'{org_end_frame}))'
            )

            # duration
            handle_duration = f'{org_end_frame} - {org_start_frame} + {frame_handle} + {frame_handle} + 1'
            first_offset_duration = f'{org_duration} - {first_offset}'
            eo_duration = f'{end_offset_end_frame} - {org_start_frame} + 1'
            df["Duration"] = (
                f'=IF(AND({frame_handle}<>"", {frame_handle}<>0), {handle_duration}, ' 
                f'IF(AND({first_offset}<>"", {first_offset}<>0), {first_offset_duration}, '
                f'IF(AND({end_offset}<>"", {end_offset}<>0), {eo_duration}, '
                f'{org_duration})))'
            )

            df["Frame Handle"] = pd.to_numeric(df["Frame Handle"])

            return df
        
        elif tab_name == "plate":
            retime_end_col = df.columns.get_loc("Retime End Frame") + 1
            retime_speed_col = df.columns.get_loc("Retime Speed") + 1

            df[start_frame_header_name] = (
                '=SUBSTITUTE( INDIRECT("R1C%s", 0), "Start Frame - ", "") - INDIRECT("R[0]C%s", 0)' % (
                    start_frame_col, handle_col
                )
            )
            df["End Frame"] = (
                '=INDIRECT("R[0]C%s", 0) + INDIRECT("R[0]C%s", 0) - 1' % (
                    start_frame_col, duration_col
                )
            )
            df["Duration"] = (
                '= IF( INDIRECT("R[0]C%s", 0) <>"", INDIRECT("R[0]C%s", 0)-INDIRECT("R[0]C%s", 0)+1, MID(INDIRECT("R[0]C%s", 0),FIND("(",INDIRECT("R[0]C%s", 0))+1,FIND(")",INDIRECT("R[0]C%s", 0),FIND("(",INDIRECT("R[0]C%s", 0))+1)-FIND("(",INDIRECT("R[0]C%s", 0))-1) - INDIRECT("R[0]C%s", 0) - INDIRECT("R[0]C%s", 0))' % (
                    retime_end_col, retime_end_col, start_frame_col, 
                    org_range_col, org_range_col, org_range_col, 
                    org_range_col, org_range_col, first_offset_col, 
                    end_offset_col
                )
            )
            df["Retime End Frame"] = (
                '=IF( INDIRECT("R[0]C%s", 0), ROUNDUP( ( MID(INDIRECT("R[0]C%s", 0),FIND("(",INDIRECT("R[0]C%s", 0))+1,FIND(")",INDIRECT("R[0]C%s", 0),FIND("(",INDIRECT("R[0]C%s", 0))+1)-FIND("(",INDIRECT("R[0]C%s", 0))-1) - INDIRECT("R[0]C%s", 0) - INDIRECT("R[0]C%s", 0) + (INDIRECT("R[0]C%s", 0) * INDIRECT("R[0]C%s", 0)) - INDIRECT("R[0]C%s", 0) ) / INDIRECT("R[0]C%s", 0), 0 ), "" )' % (
                    retime_speed_col, org_range_col, org_range_col, 
                    org_range_col, org_range_col, org_range_col, 
                    first_offset_col, end_offset_col, retime_speed_col, 
                    start_frame_col, retime_speed_col, retime_speed_col
                )
            )
        
            # Set Data Type
            df["Retime Speed"] = pd.to_numeric(df["Retime Speed"])
            df["First Frame Offset"] = pd.to_numeric(df["First Frame Offset"])
            df["End Frame Offset"] = pd.to_numeric(df["End Frame Offset"])
            df["Frame Handle"] = pd.to_numeric(df["Frame Handle"])

            return df

    def validate_data(self, parent, data_root, row_cnt, col_cnt, output_path, data):
        if not data:
            QMessageBox.warning(parent, "Excel Export", "엑셀 파일을 생성할 데이터가 없습니다.")
            logger.error("No data to export to Excel.")
            return False

        if not os.path.exists(data_root):
            QMessageBox.warning(parent, "Excel Export", "데이터 루트 경로가 유효하지 않습니다.")
            logger.error(f"Invalid data root path: {data_root}")
            return False

        if row_cnt == 0 or col_cnt == 0:
            QMessageBox.warning(parent, "Excel Export", "데이터가 유효하지 않습니다.")
            logger.error(f"Invalid Row Count: {row_cnt}, Column Count: {col_cnt}")
            return False

        if not output_path:
            QMessageBox.warning(parent, "Excel Export", "엑셀 파일을 저장할 경로가 유효하지 않습니다.")
            logger.error(f"Invalid output path: {output_path}")
            return False
        
        if not data:
            QMessageBox.warning(parent, "Excel Export", "엑셀 파일을 생성할 데이터가 없습니다.")
            logger.error("No data to export to Excel.")
            return False
    
        return True

    def load_excel(self, parent, excel_path, eval_formula=True):
        if not os.path.exists(excel_path):
            QMessageBox.warning(parent, "Excel Load", "엑셀 파일이 존재하지 않습니다.")
            return
        
        if eval_formula:
            # Eval Fomulas using xlwings
            app = xw.App(visible=False)
            book = app.books.open(excel_path)
            book.save()
            app.kill()
        
        return pd.read_excel(excel_path, index_col=None, engine='openpyxl').fillna("")