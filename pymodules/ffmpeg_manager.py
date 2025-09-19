# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from timecode import Timecode
from fractions import Fraction

# Custom Modules
try:
    import constants
    from init_logger import IOManagerLogger
except:
    from pymodules import constants
    from pymodules.init_logger import IOManagerLogger

# Set Logger
logger = IOManagerLogger(os.path.basename(__file__), constants.LOG_PATH)

os.environ["PATH"] += os.pathsep + r"W:\MTHD_core\GlobalLib\third-party\ffmpeg\4.4"


class FFMPEGManager():
    def extract_thumbnail(self, input_path, output_path):
        if not os.path.exists(input_path):
            logger.error(f"File not found: {input_path}")
            return None
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-loglevel', 'error',
            '-vf', 'thumbnail,scale=240:150,pad=max(iw\\,ih*(16/10)):ow/(16/10):(ow-iw)/2:(oh-ih)/2',
            '-frames:v', '1',
            '-y', output_path
        ]
        try:
            subprocess.run(cmd, check=True)
            return output_path
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            logger.error(f"Error processing {input_path}: {e}")
            return None
        
    def extract_mov_metadata(self, input_path):
        if not os.path.exists(input_path):
            print(f"File not found: {input_path}")
            logger.error(f"File not found: {input_path}")
            return None
        
        result = {}
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0', '-show_entries', 
            'stream_tags=timecode:stream=r_frame_rate:stream=width,height:format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', input_path
        ]
        try:
            # output = ['1920\r', '1080\r', '24/1\r', '00:03:27:23\r', '1.791667']
            output = subprocess.check_output(cmd).decode().strip().split('\n')
            width = int(output[0].strip())
            height = int(output[1].strip())
            fps = round(float(Fraction(output[2].strip())), 3)
            start_tc = output[3].strip()
            duration = round(float(output[4].strip()) * fps)
            end_tc = Timecode(fps, start_tc) + duration - 1

            result["start_tc"] = start_tc
            result["duration"] = duration
            result["fps"] = fps
            result["end_tc"] = end_tc
            result["width"] = width
            result["height"] = height
            return result
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            logger.error(f"Error processing {input_path}: {e}")
            return None
    
    def extract_mov_clip_name(self, input_path):

        if not os.path.exists(input_path):
            print(f"File not found: {input_path}")
            logger.error(f"File not found: {input_path}")
            return None
        
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'd:0', '-show_entries', 
            'stream_tags=reel_name',
            '-of', 'default=noprint_wrappers=1:nokey=1', input_path
        ]
        try:
            output = subprocess.check_output(cmd).decode().strip()
            clip_name = output if output else None
            return clip_name
        
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            logger.error(f"Error processing {input_path}: {e}")
            return None

if __name__ == "__main__":
    manager = FFMPEGManager()
    input_path = r"C:\workspace\101_S004_0010_mp0_v001.mov"
    res = manager.extract_mov_metadata(input_path)
    print(res)
    
    