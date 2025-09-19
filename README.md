# IO Manager
![main](/resources/iomanager.png)
A professional VFX pipeline tool for managing media assets, organizing sequences and MOV files according to VFX studio standards, and submitting render jobs to Deadline render farms with ShotGrid integration.

## Overview

IO Manager is a PyQt-based desktop application designed for VFX studios to streamline the process of ingesting, organizing, and processing media files. The application automates the conversion of image sequences and MOV files into standardized formats while maintaining proper color management and metadata integration with ShotGrid.

## Key Features

### Media Processing
- **Dual Format Support**: Handles both image sequences (EXR, DPX, etc.) and MOV files
- **Automated File Organization**: Organizes media files according to VFX studio naming conventions
- **Batch Processing**: Process multiple shots and sequences simultaneously
- **Color Management**: Advanced color space conversion using OCIO configs or Nuke's built-in colorspaces

### Deadline Integration
- **Render Farm Submission**: Submit processing jobs to Deadline render farm instead of local processing
- **Job Management**: Track and manage render jobs through Deadline's distributed rendering system
- **Resource Optimization**: Utilize studio render farm resources for heavy processing tasks

### ShotGrid Integration
- **Project Data Sync**: Automatically fetch project settings (FPS, codec, colorspace) from ShotGrid
- **Metadata Registration**: Register processed media metadata directly to ShotGrid database
- **Version Management**: Handle shot versioning and status updates
- **User Authentication**: Secure login system integrated with studio user management

### Advanced Features
- **Excel Integration**: Import/export shot data via Excel spreadsheets for external review
- **Thumbnail Generation**: Automatic thumbnail creation for quick visual reference
- **Frame Range Management**: Flexible frame range handling with offset controls
- **Quality Control**: Built-in validation tools for media integrity checking

## System Requirements

### Dependencies
- Python 3.7 or higher
- PySide2 (Qt for Python)
- OpenEXR Python bindings
- Shotgun API3
- Additional VFX pipeline tools (Nuke, FFmpeg)
- Windows (Primary)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/junopark00/IOManager.git
   cd IOManager
   ```

2. **Install Python dependencies:**
   ```bash
   pip install PySide2 shotgun_api3 OpenEXR timecode
   ```

3. **Configure ShotGrid connection:**
   - Edit `pymodules/sg_manager.py`
   - Update ShotGrid server URL and API credentials:
     ```python
     script_name = "your_script_name"
     script_key = "your_script_key" 
     server_path = "https://your-studio.shotgrid.autodesk.com"
     ```

4. **Configure Deadline connection:**
   - Edit `pymodules/deadline_constants.py`
   - Set Deadline server IP and port:
     ```python
     DEADLINE_IP = "your.deadline.server.ip"
     DEADLINE_PORT = "8082"
     ```

5. **Set up project configuration:**
   - Modify `config.json` for project-specific settings
   - Configure default paths in `pymodules/constants.py`

## Usage

### Getting Started

1. **Launch the application:**
   ```bash
   python io-manager.py
   ```

2. **Login:** Enter your studio credentials when prompted

3. **Select Project:** Choose your active project from the dropdown menu

### Processing Plates

1. **Scan Folder Tab:**
   - Click "Scan Folder" to select source media directory
   - Application automatically detects sequences vs. MOV files
   - Review detected media in the table view

2. **Configure Settings:**
   - **Render Settings**: Frame rate, codec, resolution
   - **Color Management**: Input/output colorspaces, OCIO configuration
   - **Frame Ranges**: Start/end frames, handles, offsets

3. **Submit Jobs:**
   - Click "Render" to submit processing jobs to Deadline
   - Monitor job progress through Deadline Monitor
   - Processed files are automatically organized and registered in ShotGrid

### Processing Editorial Content

1. **Edit Tab:**
   - Select editorial source folder
   - Configure episode/sequence/shot naming
   - Set version information and descriptions

2. **Batch Processing:**
   - Use Excel integration for bulk shot management
   - Import shot lists and metadata
   - Process multiple editorial elements simultaneously

## Configuration

### Project Settings
The application reads project-specific settings from ShotGrid including:
- Default frame rates and codecs
- Color management profiles
- Output resolutions and formats
- File naming conventions

### Color Management
Supports both OCIO-based and Nuke native color management:
- **OCIO**: Studio-standard color configs with LUT support
- **Nuke Default**: Built-in Nuke colorspaces for simpler workflows

### File Organization
Processed files are organized using studio-standard directory structures:
```
V:/PROJECT_NAME/
├── shots/
│   ├── SEQUENCE/
│   │   ├── SHOT_NAME/
│   │   │   ├── plate/
│   │   │   ├── comp/
│   │   │   └── mov/
```

## Architecture

### Core Modules
- **io-manager.py**: Main application entry point and UI controller
- **ui.py**: PyQt interface definitions and layout management  
- **sg_manager.py**: ShotGrid API integration and data management
- **deadline_manager.py**: Deadline render farm job submission
- **nuke_manager.py**: Nuke script generation for processing jobs
- **excel_manager.py**: Excel spreadsheet import/export functionality

### Render Pipeline
1. **Media Detection**: Scan source directories for sequences/MOV files
2. **Metadata Extraction**: Read timecode, resolution, frame range information
3. **Job Generation**: Create Nuke scripts for processing tasks
4. **Deadline Submission**: Submit jobs to render farm with proper dependencies
5. **Post-Processing**: Organize outputs and update ShotGrid records

## Troubleshooting

### Common Issues

**Connection Problems:**
- Verify ShotGrid API credentials and server accessibility
- Check Deadline server connection and port configuration
- Ensure network firewall allows communication

**File Processing Errors:**
- Confirm source media file permissions and accessibility
- Verify output directory write permissions
- Check color management configuration files

**Performance Issues:**
- Monitor Deadline render farm capacity
- Optimize batch job sizes for available resources
- Review network bandwidth for large file transfers

### Logging
Application logs are written to `C:/io-manager/io-manager.log` with detailed debug information for troubleshooting pipeline issues.

