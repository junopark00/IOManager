# -*- coding: utf-8 -*-

import os

# Custom Modules
try:
    import constants
    from init_logger import IOManagerLogger
except:
    from pymodules import constants
    from pymodules.init_logger import IOManagerLogger

# Set Logger
logger = IOManagerLogger(os.path.basename(__file__), constants.LOG_PATH)


def get_comp_cmd(paths, row_data, render_settings, sg_proj_data, comp_temp_path):
    nuke_shot_work_path, nuke_plate_path, default_nk_file, exr_output_path, mov_output_path, cube_path = paths
    
    first_frame = row_data.get("Start Frame")
    last_frame = row_data.get("End Frame")
    use_ocio = render_settings.get('use_ocio_colorspace')
    ocio_path = render_settings.get('ocio_config')
    input_color = render_settings.get('input_colorspace')
    output_color = render_settings.get('output_colorspace')
    exr_datatype = sg_proj_data.get('sg_exr_data_type')
    exr_compression = sg_proj_data.get('sg_exr_format')
    mov_codec = sg_proj_data.get('sg_mov_codec')
    mov_fps = sg_proj_data.get('sg_mov_fps')
    exr_resolution = sg_proj_data.get('sg_exr_resolution')

    cmd = f"""
import os, re
import nuke

use_ocio = {use_ocio}
cube_path = '{cube_path}'
nuke_shot_work_path = '{nuke_shot_work_path.replace(os.sep, "/")}'
nuke_plate_path = '{nuke_plate_path.replace(os.sep, "/")}'
input_color = '{input_color}'
output_color = '{output_color}'
ocio_path = '{ocio_path.replace(os.sep, "/") if ocio_path else ''}'
f_frame = int({first_frame})
l_frame = int({last_frame})
exr_datatype = '{exr_datatype}'
exr_compression = '{exr_compression}'
exr_output_path = '{exr_output_path.replace(os.sep, "/")}'
mov_output_path = '{mov_output_path.replace(os.sep, "/")}'
mov_codec = '{mov_codec}'
mov_fps = {mov_fps}
comp_temp_path = '{comp_temp_path.replace(os.sep, "/")}'

nuke.scriptOpen('{default_nk_file}')
"""
    if use_ocio:
        cmd += """
# Set OCIO
nuke.Root().knob('colorManagement').setValue('OCIO')
nuke.Root().knob('OCIO_config').setValue('custom')
nuke.Root().knob('customOCIOConfigPath').setValue(ocio_path)
"""

    cmd += """
# Set Plate Node
plate_node = nuke.toNode('plate')
if not plate_node:
    plate_node = nuke.toNode('Read1')
xpos = plate_node['xpos'].value()
ypos = plate_node['ypos'].value()

# Get Next Nodes
next_nodes = plate_node.dependent()
p = re.compile('((.+)[_|.]([#]+|[%][0-9][0-9][d])[.](.+) \d+[-]\d+)')
regular = p.match(nuke_plate_path)
if not regular and not os.path.isfile(nuke_plate_path):
    seqs = nuke.getFileNameList(os.path.dirname(nuke_plate_path))
    for seq_name in seqs:
        _reg = p.match(seq_name)
        if _reg:
            nuke_plate_path = os.path.dirname(nuke_plate_path) + '/' + seq_name
            break
            
# Set New Read Node
read_node = nuke.createNode('Read')
read_node['file'].fromUserText(nuke_plate_path)
if input_color == 'raw':
    read_node['raw'].setValue(True)
else:
    read_node['colorspace'].setValue(input_color)
read_node['xpos'].setValue(xpos)
read_node['ypos'].setValue(ypos)
for next_node in next_nodes:
    i = next_node.dependencies().index(plate_node)
    next_node.setInput(i, read_node)
    
# Delete Plate Node
nuke.delete(plate_node)
read_node['name'].setValue('plate')

mdata = read_node.metadata()
plate_format_name = 'current_plate_format'
plate_format = str(mdata.get('input/width')) + ' ' + str(mdata.get('input/height')) + ' ' + plate_format_name
nuke.addFormat(plate_format)
nuke.Root()['format'].setValue(plate_format_name)
nuke.Root()['first_frame'].setValue(f_frame)
nuke.Root()['last_frame'].setValue(l_frame)

# Set OCIO and Cube
if cube_path and use_ocio:
    ocio_file_transform = nuke.toNode('OCIOFileTransform1')
    ocio_file_transform['file'].fromUserText(cube_path)
elif cube_path and not use_ocio:
    vectorfield = nuke.toNode('Vectorfield1')
    vectorfield['vfield_file'].fromUserText(cube_path)
    vectorfield['file_type'].setValue('cube')
    if input_color == 'raw':
        vectorfield['colorspaceIn'].setValue('linear')
    else:
        vectorfield['colorspaceIn'].setValue(input_color)
    if output_color == 'raw':
        vectorfield['colorspaceOut'].setValue('linear')
    else:
        vectorfield['colorspaceOut'].setValue(output_color)

# Set Write_exr1 Node
write_exr1 = nuke.toNode('Write_exr1')
if write_exr1:
    write_exr1['file'].setValue(exr_output_path)
    if output_color == 'raw':
        write_exr1['raw'].setValue(True)
    else:
        write_exr1['colorspace'].setValue(output_color)
    write_exr1['file_type'].setValue('exr')
    if exr_datatype:
        write_exr1['datatype'].setValue(exr_datatype)
    if exr_compression:
        write_exr1['compression'].setValue(exr_compression)
    write_exr1['create_directories'].setValue(True)
    
# Set Write_mov1 Node
write_mov1 = nuke.toNode('Write_mov1')
if write_mov1:
    write_mov1['file'].setValue(mov_output_path)
    if output_color == 'raw':
        write_mov1['raw'].setValue(True)
    else:
        write_mov1['colorspace'].setValue(output_color)
    write_mov1['file_type'].setValue('mov')
    write_mov1['create_directories'].setValue(True)

    if mov_codec.lower().startswith('prores'):
        write_mov1['mov64_codec'].setValue('appr')
        write_mov1['mov_prores_codec_profile'].setValue(mov_codec)
    elif mov_codec.lower().startswith('h264'):
        write_mov1['mov64_codec'].setValue('h264')
    
    write_mov1['fps'].setValue(mov_fps)
nuke.scriptSaveAs(nuke_shot_work_path, overwrite=1)

if os.path.exists(comp_temp_path):
    os.remove(comp_temp_path)
"""
    return cmd

def get_render_cmd(paths, row_data, render_settings, project_data):
    render_nk_path, data_seq, plate_path, png_path, jpg_path, mov_path, cube_path = paths
    
    # Set Row Data
    first_frame = row_data.get("Start Frame")
    last_frame = row_data.get("End Frame")
    org_range = row_data.get("Org Range")
    org_sframe = org_range.split('-')[0]
    org_eframe = org_range.split('-')[1].split('\n')[0]
    first_frame_offset = row_data.get("First Frame Offset") if row_data.get("First Frame Offset") else 0
    end_frame_offset = row_data.get("End Frame Offset") if row_data.get("End Frame Offset") else 0
    retime_end_frame = row_data.get("Retime End Frame") if row_data.get("Retime End Frame") else last_frame
    shot_name = row_data.get("Shot Name", "")
    
    # Set Project Data
    project_name = project_data.get('name', '')
    
    aspect_ratio = project_data.get('sg_aspect_ratio', '2:1')
    aspect_ratio_y = "2"
    try:
        aspect_ratio_x = aspect_ratio.split(':')[0]
    except:
        aspect_ratio_x = "2"
        
    resolution = project_data.get('sg_exr_resolution')
    resolution_x = resolution.split('*')[0]
    resolution_y = resolution.split('*')[1]
    
    # Set Render Settings
    use_ocio = render_settings.get('use_ocio_colorspace')
    ocio_path = render_settings.get('ocio_config')
    input_color = render_settings.get('input_colorspace')
    output_color = render_settings.get('output_colorspace')
    fps = render_settings.get('fps')
    codec = render_settings.get('codec')
    reformat_preset = render_settings.get('reformat_preset')
    if reformat_preset == 'Original':
        reformat_x = 0
        reformat_y = 0
    else:
        reformat_x = render_settings.get('reformat_x')
        reformat_y = render_settings.get('reformat_y')
    crop_preset = render_settings.get('crop_preset')
    if crop_preset == 'Custom':
        crop_x = render_settings.get('crop_x')
        crop_y = render_settings.get('crop_y')
    else:
        crop_x = 0
        crop_y = 0
    aspect_mode = render_settings.get('aspect_mode') # None, Extend Top/Bottom, Crop Left/Right
    resize_target = render_settings.get('resize_target') # all, mov
    
    cmd = f"""
import nuke
import os
import re
import json
config_path = "W:/MTHD_core/standalone/io-manager/config.json"
use_ocio = {use_ocio}
nk_path = '{render_nk_path}'
data_seq = '{data_seq}'
plate_path = '{plate_path}'
if os.path.splitext(plate_path)[-1] == '.None':
    raise BaseException('프로젝트 설정에 Out Plate Extension이 정의되지 않았습니다. 렌더링을 진행할 수 없습니다.')
jpg_path = '{jpg_path}'
mov_path = '{mov_path}'
png_path = '{png_path}'
cube_path = '{cube_path}'
first_frame = {first_frame}
last_frame = {last_frame}
org_sframe = {org_sframe}
org_eframe = {org_eframe}
seq_info = '{first_frame}-{last_frame}'
ocio_path = '{ocio_path.replace(os.sep, "/")}'
input_color = '{input_color}'
output_color = '{output_color}'
fps = {fps}
first_frame_offset = {first_frame_offset}
end_frame_offset = {end_frame_offset}
retime_end_frame = {retime_end_frame}
reformat_preset = '{reformat_preset}'
reformat_x = {reformat_x}
reformat_y = {reformat_y}
crop_preset = '{crop_preset}'
crop_x = {crop_x}
crop_y = {crop_y}
codec = '{codec}'
slate_nk = '{constants.DEFAULT_SLATE}'
project_name = '{project_name}'
shot_name = '{shot_name}'
aspect_ratio_x = float({aspect_ratio_x})
aspect_mode = '{aspect_mode}'
resolution_x = {resolution_x}
resolution_y = {resolution_y}
resize_target = '{resize_target}'

# Load Config
with open(config_path, 'r') as f:
    config = json.load(f)
    
config = config.get(project_name, dict())
"""
    if use_ocio:
        cmd += """
nuke.Root().knob('colorManagement').setValue('OCIO')
nuke.Root().knob('OCIO_config').setValue('custom')
nuke.Root().knob('customOCIOConfigPath').setValue(ocio_path)
"""
    else:
        cmd += """
nuke.Root().knob('colorManagement').setValue('Nuke')
nuke.Root().knob('OCIO_config').setValue('nuke-default')
"""
    cmd += """
read_node = nuke.createNode('Read')
read_node['file'].fromUserText(data_seq)
if input_color == 'raw':
    read_node['raw'].setValue(True)
else:
    read_node['colorspace'].setValue(input_color)
read_node['frame_mode'].setValue('start at')
read_node['frame'].setValue(str(first_frame))
read_node['label'].setValue(shot_name)
read_node['xpos'].setValue(0)
read_node['ypos'].setValue(0)

plate_width = read_node.width()
plate_height = read_node.height()

mdata = read_node.metadata()
if not reformat_x and not reformat_y:
    reformat_x = mdata.get('input/width', 0)
    reformat_y = mdata.get('input/height', 0)

# Set MOV Time Offset
offset_node = nuke.createNode('TimeOffset')
offset_node['time_offset'].setValue(-int(first_frame_offset))
offset_node['xpos'].setValue(0)
offset_node['ypos'].setValue(100)
offset_node.setInput(0, read_node)

# Set Frame Range
frame_range_node = nuke.createNode('FrameRange')
frame_range_node.setInput(0, offset_node)
frame_range_node['first_frame'].setValue(int(first_frame))
frame_range_node['last_frame'].setValue(int(last_frame))
frame_range_node['xpos'].setValue(0)
frame_range_node['ypos'].setValue(150)
frame_range_node.setInput(0, offset_node)

# Set MOV Reformat
reformat = nuke.createNode('Reformat')
reformat['type'].setValue('to box')
reformat['box_fixed'].setValue(True)
reformat['black_outside'].setValue(True)

if reformat_preset == 'Original':
    reformat['box_width'].setValue(plate_width)
    reformat['box_height'].setValue(plate_height)
else:
    reformat['box_width'].setValue(reformat_x)
    reformat['box_height'].setValue(reformat_y)
    
reformat['xpos'].setValue(0)
reformat['ypos'].setValue(200)
reformat.setInput(0, frame_range_node)

# Set Aspect Ratio
aspect_crop = nuke.createNode('Reformat')
if aspect_mode == 'Crop Left/Right':
    reformat_height = reformat['box_height'].value()  
    aspect_mode_width = int(reformat_height) * aspect_ratio_x
    aspect_mode_height = reformat_height
    
    if aspect_mode_width > plate_width:
        aspect_mode_width = plate_width
    
    aspect_crop['ypos'].setValue(250)
    aspect_crop['type'].setValue('to box')
    aspect_crop['box_fixed'].setValue(True)
    aspect_crop['box_width'].setValue(aspect_mode_width)
    aspect_crop['box_height'].setValue(aspect_mode_height)
    aspect_crop['resize'].setValue('height')
    
    aspect_crop.setInput(0, reformat)
else:
    aspect_crop['disable'].setValue(True)

# Set MOV Crop
crop = nuke.createNode('Crop')
if crop_preset == 'Original':
    crop['disable'].setValue(True)
elif crop_preset == 'Custom':
    crop['preset'].setValue('format')
    crop['box'].setExpression('(this.input0.box_width - ' + str(crop_x) + ') / 2', 0)
    crop['box'].setExpression('(this.input0.box_height - ' + str(crop_y) + ') / 2', 1)
    crop['box'].setExpression('this.input0.box_width - ((this.input0.box_width - ' + str(crop_x) + ') / 2)', 2)
    crop['box'].setExpression('this.input0.box_height - ((this.input0.box_height - ' + str(crop_y) + ') / 2)', 3)
else:
    crop['preset'].setValue(crop_preset)
crop['reformat'].setValue(True)
crop['intersect'].setValue(True)
crop['crop'].setValue(True)
crop['xpos'].setValue(0)
crop['ypos'].setValue(300)
crop.setInput(0, aspect_crop)

###### Set OCIO Cube ######
if cube_path and use_ocio:
    ocio_colorspace = nuke.createNode("OCIOColorSpace")
    ocio_colorspace['in_colorspace'].setValue(config.get('ocio_in', 'ACES - ACEScg'))
    ocio_colorspace['out_colorspace'].setValue(config.get('ocio_out', 'Output - Rec.709'))
    ocio_colorspace['xpos'].setValue(0)
    ocio_colorspace['ypos'].setValue(350)
    ocio_colorspace.setInput(0, crop)
    ocio_transform = nuke.createNode("OCIOFileTransform")
    ocio_transform['file'].fromUserText(cube_path)
    ocio_transform['working_space'].setValue(config.get('EXR_colorspace', 'ACES - ACEScg'))
    ocio_transform['xpos'].setValue(0)
    ocio_transform['ypos'].setValue(400)
    ocio_transform.setInput(0, ocio_colorspace)
    
    nuke.nodePaste(slate_nk)
    slate_node = nuke.toNode('Plate_Slate1')
    slate_node['show'].setValue(project_name)
    slate_node['shot'].setValue(shot_name)
    slate_node['box_width'].setValue(resolution_x)
    slate_node['box_height'].setValue(resolution_y)
    slate_node['xpos'].setValue(0)
    slate_node['ypos'].setValue(450)
    slate_node.setInput(0, ocio_transform)
elif cube_path and not use_ocio:
    vectorfield = nuke.createNode('Vectorfield')
    vectorfield['vfield_file'].fromUserText(cube_path)
    color_in = config.get('EXR_colorspace').lower()
    color_out = config.get('MOV_colorspace').lower()
    vectorfield['colorspaceIn'].setValue(color_in if color_in != 'raw' else 'linear')
    vectorfield['colorspaceOut'].setValue(color_out if color_out != 'raw' else 'linear')
    vectorfield['xpos'].setValue(0)
    vectorfield['ypos'].setValue(350)
    vectorfield.setInput(0, crop)
    nuke.nodePaste(slate_nk)
    slate_node = nuke.toNode('Plate_Slate1')
    slate_node['show'].setValue(project_name)
    slate_node['shot'].setValue(shot_name)
    slate_node['box_width'].setValue(resolution_x)
    slate_node['box_height'].setValue(resolution_y)
    slate_node['xpos'].setValue(0)
    slate_node['ypos'].setValue(400)
    slate_node.setInput(0, vectorfield)
else:
    nuke.nodePaste(slate_nk)
    slate_node = nuke.toNode('Plate_Slate1')
    slate_node['show'].setValue(project_name)
    slate_node['shot'].setValue(shot_name)
    slate_node['box_width'].setValue(resolution_x)
    slate_node['box_height'].setValue(resolution_y)
    slate_node['xpos'].setValue(0)
    slate_node['ypos'].setValue(350)
    slate_node.setInput(0, crop)
if project_name == "SCD":
    slate_node['mask_opacity'].setValue('0%')
    slate_node['bar_height'].clearAnimated()
    slate_node['bar_height'].setValue(100)
    slate_node['disable'].setValue(True)

# Set MOV Write
mov_write = nuke.createNode('Write')
mov_write['name'].setValue('WriteMOV')
mov_write['file'].setValue(mov_path)
mov_write['file_type'].setValue('mov')
if output_color == 'raw':
    mov_write['raw'].setValue(True)
else:
    mov_write['colorspace'].setValue(output_color)
_codec_profile = None
if codec.lower().startswith('prores'):
    _codec = "appr"
    _codec_profile = codec
elif codec.lower().startswith('avid'):
    _codev = "AVdn"
    _codec_profile = 'DNxHD ' + codec.split(' - ')[-1]
elif codec.lower() == 'h.264':
    _codec = "h264"
elif codec.lower() == 'mpeg-4':
    _codec = "mp4v"
elif codec.lower() == 'photo -jpeg':
    _codec = "jpeg"
elif codec.lower() == 'png':
    _codec = "png"
mov_write['mov64_codec'].setValue(_codec)
if _codec_profile:
    try:
        mov_write['mov_prores_codec_profile'].setValue(_codec_profile)
    except:
        pass
    try:
        mov_write['mov64_dnxhd_codec_profile'].setValue(_codec_profile)
    except:
        pass
try:
    mov_write['mov64_fps'].setValue(fps)
except:
    pass
try:
    mov_write['mov32_fps'].setValue(fps)
except:
    pass

mov_write['xpos'].setValue(0)
mov_write['ypos'].setValue(500)
mov_write.setInput(0, slate_node)
    
# Set Plate Write
plate_write = nuke.createNode('Write')
plate_write['name'].setValue('WritePLATE')
plate_write['file'].setValue(plate_path)
plate_write['channels'].setValue('all')
if input_color == 'raw':
    plate_write['raw'].setValue(True)
else:
    plate_write['colorspace'].setValue(input_color)
# splitext
_plate_ext = plate_path.split('.')[-1].lower()
if _plate_ext in ['exr', 'dpx']:
    plate_write['file_type'].setValue(_plate_ext)
elif _plate_ext in ['jpg', 'jpeg']:
    plate_write['file_type'].setValue('jpeg')
    plate_write['_jpeg_quality'].setValue('1')
    plate_write['_jpeg_sub_sampling'].setValue('4:4:4')
else:
    plate_write['file_type'].setValue('dpx')
plate_write['xpos'].setValue(100)
plate_write['ypos'].setValue(500)

if resize_target == 'mov':
    plate_write.setInput(0, frame_range_node)
else:
    plate_write.setInput(0, crop)
    
_datatype = mdata.get('input/bitsperchannel')
_compression = mdata.get('exr/compressionName')
if _datatype:
    plate_write['datatype'].setValue(_datatype) if plate_write.knob('datatype') else None
if _compression:
    plate_write['compression'].setValue(_compression) if plate_write.knob('compression') else None
    
# Set JPG Write
jpg_write = nuke.createNode('Write')
jpg_write['name'].setValue('WriteJPG')
jpg_write['file'].setValue(jpg_path)
if output_color == 'raw':
    jpg_write['raw'].setValue(True)
else:
    jpg_write['colorspace'].setValue(output_color)
jpg_write['file_type'].setValue('jpeg')
jpg_write['_jpeg_quality'].setValue('1')
jpg_write['_jpeg_sub_sampling'].setValue('4:4:4')
jpg_write['xpos'].setValue(-100)
jpg_write['ypos'].setValue(500)

if resize_target == 'mov':
    jpg_write.setInput(0, frame_range_node)
else:
    jpg_write.setInput(0, crop)
    
# Set PNG Write
png_write = nuke.createNode('Write')
png_write['name'].setValue('WritePNG')
png_write['file'].setValue(png_path)
if output_color == 'raw':
    png_write['raw'].setValue(True)
else:
    png_write['colorspace'].setValue(output_color)
png_write['file_type'].setValue('png')
png_write['xpos'].setValue(-200)
png_write['ypos'].setValue(500)

if resize_target == 'mov':
    png_write.setInput(0, frame_range_node)
else:
    png_write.setInput(0, crop)
    
write_node = nuke.toNode('Write1')
if write_node:
    write_node['file'].setValue(mov_path)
    if output_color == 'raw':
        write_node['raw'].setValue(True)
    else:
        write_node['colorspace'].setValue(output_color)
    write_node['file_type'].setValue('mov')
    
nuke.scriptSave(nk_path)
result = dict()
result['nk_path'] = nk_path
result['seq_info'] = seq_info
result['plate_path'] = plate_path
result['jpg_path'] = jpg_path
result['mov_path'] = mov_path
print('data_start')
print(result)
print('data_end')
"""
    
    return cmd