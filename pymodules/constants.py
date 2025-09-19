# -*- coding: utf-8 -*-


## UPLOADED VERSION STATUS
UPLOADED_VERSION_STATUS = "po"

## PATHS
DEFAULT_DRIVE = "V:/"

## Log Path
LOG_PATH = "C:/io-manager/io-manager.log"

## Default Slate
DEFAULT_SLATE = "C:/io-manager/resources/nk_files/Plate_Slate.nk"

## COLORSPACE
# This data based on Nuke 14.1v1
NUKE_DEFAULT_COLORSPACES = [
    "raw", "linear", "sRGB", "rec709", "Cineon", "Gamma1.8", "Gamma2.2", "Gamma2.4", "Gamma2.6",
    "Panalog", "REDlog", "ViperLog", "AlexaV3LogC", "PLogLin", "SLog", "SLog1", "SLog2", "SLog3",
    "CLog", "Log3G10", "Log3G12", "HybridLogGamma", "Protune", "BT1886", "st2084", "Blackmagic Film Generation 5", "ARRILogC4"
]

## TABLE HEADERS
HEADERS = [
    "Render", "Thumbnail", "Scan Data", "Clip Name", "Sequence", "Shot Name", 
    "Type", "Version", "Version Description", "Cube", "Plate Resolution",
    "TimeCode In", "TimeCode Out", "Org Range", "Start Frame", "End Frame", 
    "Duration", "Frame Handle", "First Frame Offset", 
    "End Frame Offset", "Retime End Frame", "Retime TimeCode Out", 
    "Retime Speed"
]

EDIT_HEADERS = [
    "Render", "Thumbnail", "Scan Data", "Episode", "Sequence", "Shot Name", "Type", "Version", "Date", "Version Description",
    "Org Range", "Start Frame", "End Frame", "Duration", "Frame Handle", "First Frame Offset", "End Frame Offset",
]

# Hide When Simple View
IGNORE_HEADERS = [
    "Retime End Frame", "Retime TimeCode Out", "Retime Speed"
]

# Read Only Fields
READONLY_HEADERS = [
    "Thumbnail", "Scan Data", "TimeCode In", "TimeCode Out", "Org Range", "Start Frame", "End Frame", "Duration", 
    "Retime End Frame", "Retime TimeCode Out", "Clip Name", "Plate Resolution"
    #"PLATE", "JPG", "MOV", "Shotgrid", "Connected"
]

READONLY_CELL_HEADERS = [
    "Scan Data", "TimeCode In", "TimeCode Out", "Org Range", "Start Frame", "End Frame", "Duration",
]

## REFORMAT PRESETS
REFORMAT_PRESETS = [
    "Original", "Custom",
    "HD_1280x720", "FHD_1920x817", "FHD_1920x1080",
    "2K_2048x871", "2K_2048x1080", "2K_2048x1152", "2K_2048x1412", "2K_2048x1556",
    "4K_4096x2160", "4K_4096x3112"
]

## CROP PRESETS
CROP_PRESETS = [
    "Original", "Custom", "Square", "4:3", "16:9", "14:9", "1.66:1", "1.85:1", "2.35:1"
]

## FPS PRESETS
FPS_PRESETS = [
    "Custom", "23.976", "24", "25", "29.97", "30", "50", "59.94", "60", "120"
]

## CODECS
CODECS = [
    "ProRes 4:4:4:4 XQ 12-bit", "ProRes 4:4:4:4 12-bit", "ProRes 4:2:2 HQ 10-bit", "ProRes 4:2:2 10-bit",
    "ProRes 4:2:2 LT 10-bit", "ProRes 4:2:2 Proxy 10-bit", "H.264", "Photo - JPEG", "MPEG-4",
    "Avid DNxHD Codec - 422 8-bit 36Mbit", "Avid DNxHD Codec - 422 8-bit 145Mbit", "Avid DNxHD Codec - 422 8-bit 220Mbit",
    "Avid DNxHD Codec - 422 10-bit 220Mbit", "Avid DNxHD Codec - 444 10-bit 440Mbit"
]

## OCIO CONFIG
DEFAULT_OCIO_CONFIG = "V:/ORV/stuff/spec/_OCIO/config.ocio"

## SEQUENCE TYPES
SEQUENCE_TYPES = [
    ".jpg", ".exr", ".dpx", ".png",
]
