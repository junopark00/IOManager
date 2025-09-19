# -*- coding: utf-8 -*-

import os
import re
import sys

import shotgun_api3 as sg

# Custom Modules
try:
    import constants
    from init_logger import IOManagerLogger
except:
    from pymodules import constants
    from pymodules.init_logger import IOManagerLogger

# Set Logger
logger = IOManagerLogger(os.path.basename(__file__), constants.LOG_PATH)

script_name = "your_script_name"
script_key = "your_script_key"
server_path = "https://site.shotgrid.autodesk.com"

con = sg.Shotgun(server_path, script_name=script_name, api_key=script_key)

def get_user_by_email(email):
    sg_user = con.find_one("HumanUser", [["email", "is", email]], ["name", "department", "email"])
    if not sg_user:
        logger.error(f"ShotGrid user not found: {email}")
        return None
    return sg_user

def get_active_projects():
    # status active
    sg_projects = con.find("Project", [["sg_status", "is", "active"]], ["name"])
    if not sg_projects:
        logger.error("No active projects found in ShotGrid.")
        return None
    
    active_projects = []
    for project in sg_projects:
        active_projects.append(project.get("name"))
    return active_projects

def get_project_data(project_name):
    fields = [
        'name',
        'sg_mov_fps',
        'sg_out_plate_ext',
        'sg_exr_color_space',
        'sg_exr_format',
        'sg_exr_data_type',
        'sg_exr_resolution',
        'sg_mov_color_space',
        'sg_ocio',
        'sg_ocio_path',
        'sg_mov_codec',
        'sg_default_comp_nk',
        'sg_aspect_ratio'
        # 'sg_mov_slate_nk',
    ]
    sg_project = con.find_one(
        "Project", 
        [["name", "is", project_name], ["sg_status", "is", "active"]], 
        fields
    )
    
    if not sg_project:
        logger.error(f"Project not found: {project_name}")
        return None
    
    return sg_project

def find_or_create_sequence(sg_project, sequence):
    sg_seq = con.find_one(
        "Sequence",
        [["project", "is", sg_project], ["code", "is", sequence]]
    )
    if sg_seq:
        return sg_seq

    return con.create(
        "Sequence",
        {"project": sg_project, "code": sequence}
    )

def find_or_create_shot(sg_project, sequence_name, shot_code):
    sg_sequence = find_or_create_sequence(sg_project, sequence_name)

    sg_shot = con.find_one(
        "Shot",
        [["project", "is", sg_project], ["code", "is", shot_code], ["sg_sequence", "is", sg_sequence]], 
        ["project", "code", "sg_sequence"]
    )
    
    if sg_shot:
        return sg_shot
    
    return con.create(
        "Shot",
        {"project": sg_project, "code": shot_code, "sg_sequence": sg_sequence}
    )

def find_or_create_step(step_name, step_short_code):
    sg_step = con.find_one(
        "Step",
        [["entity_type", "is", "Shot"], ["code", "is", step_name]]
    )
    if sg_step:
        return sg_step

    return con.create(
        "Step",
        {"entity_type": "Shot", "code": step_name, "short_name": step_short_code}
    )

def find_or_create_task(
        sg_project, sg_shot, step_name, step_short_code, task_name
):
    
    filters = [
        ["project", "is", sg_project], ["entity", "is", sg_shot], 
        ["step", "name_is", step_name], ["content", "is", task_name]
    ]

    fields = ["project", "content", "entity"]

    sg_task = con.find_one("Task", filters, fields)

    if sg_task:
        return sg_task
    
    sg_step = find_or_create_step(step_name, step_short_code)
    return con.create(
        "Task",
        {"project": sg_project, "entity": sg_shot, 
         "step": sg_step, "content": task_name}
    )

def validate_versions(project_name, sequence_name, shot_code, _type):
    version_pattern = f"{shot_code}_{_type}_v"

    v_filters = [
        ["project.Project.name", "is", project_name],
        ["entity.Shot.sg_sequence.Sequence.code", "is", sequence_name],
        ["entity.Shot.code", "is", shot_code],
        ["code", "starts_with", version_pattern]
    ]
    v_fields = ["code"]
    
    try:
        sg_versions = con.find("Version", v_filters, v_fields)
    except:
        version_list = None
    
    if not sg_versions:
        version_list = None
    
    version_list = sorted([version.get("code") for version in sg_versions if version.get("code")])
    
    s_filters = [
        ["project.Project.name", "is", project_name],
        ["sg_sequence.Sequence.code", "is", sequence_name],
        ["code", "is", shot_code]
    ]
    s_fields = ["sg_luts"]
    cube_name = None
    try:
        sg_shot = con.find_one("Shot", s_filters, s_fields)
    except:
        cube_name = None
    
    if sg_shot:
        cube_name = sg_shot.get("sg_luts")
    
    return version_list, cube_name

def retake_low_versions(project_name, shot_code, task_name, _type, status="retake"):
    err_list = []
    version_pattern = f"{shot_code}_{_type}_v"
    
    filters = [
        ["project.Project.name", "is", project_name],
        ["entity.Shot.code", "is", shot_code],
        ["sg_task.Task.content", "is", task_name],
        ["code", "starts_with", version_pattern]
    ]
    fields = ["code"]
    
    try:
        sg_versions = con.find("Version", filters, fields)
    except Exception as e:
        err_list.append(f"Failed to find versions for {shot_code}: {e}")
        return err_list
        
    if not sg_versions:
        return err_list
    
    for version in sg_versions:
        try:
            con.update("Version", version["id"], {"sg_status_list": status})
        except Exception as e:
            err_list.append(f"Failed to update version: {version.get('code')} - {e}")
            continue
        
    return err_list

def get_plate_versions(sg_shot, shot_code, current_version):
    err_list = []
    plate_list = [current_version]
    version_pattern = f"{shot_code}_"
    
    filters = [
        ["entity", "is", sg_shot],
        ["sg_task.Task.content", "is", "plate"],
        ["sg_status_list", "is", "po"],
        ["code", "starts_with", version_pattern]
    ]
    fields = ["code"]
    
    try:
        po_versions = con.find("Version", filters, fields)
    except Exception as e:
        err_list.append(f"Failed to find versions for {shot_code}: {e}")
        return err_list
    
    if po_versions:
        pattern = re.compile(rf'{shot_code}_(rp\d|mp\d|sp\d)(_v\d+)')
        for po_version in po_versions:
            code = po_version.get("code")
            if not code:
                continue
            
            match = pattern.match(code)
            if not match:
                continue
            
            plate_list.append(match.group(1) + match.group(2))
            
        if len(plate_list) <= 1:
            err_list.append(f"No additional plate versions found for {shot_code}")
        
        plate_list = sorted(plate_list, key=sort_key)
    
    plate_versions_str = "\n".join(plate_list)
    
    try:
        con.update("Shot", sg_shot["id"], {"sg_plate_versions": plate_versions_str})
    except Exception as e:
        err_list.append(f"Failed to update plate versions for {shot_code}: {e}")
    
    return err_list
        
def sort_key(item):
    try:
        prefix, rest = item.split('_')
    except ValueError:
        return (3, 0, 0)
    number = int(''.join(filter(str.isdigit, prefix)))
    version = int(rest.replace('v', ''))
    
    priority = {'rp': 0, 'mp': 1, 'sp': 2}
    
    prefix_key = prefix[:2]
    priority_value = priority.get(prefix_key, 3)  # Default to 3 for non-matching prefixes
    
    return (priority_value, -number, -version) 

def update_version_status(sg_version, status):
    data = {"sg_status_list": status}
    
    try:
        updated = con.update("Version", sg_version["id"], data)
    except:
        updated = None
        
    return updated

def get_shot_info(project_name, sg_shot):
    shot_info = con.find_one(
        "Shot", 
        [["project.Project.name", "is", project_name], ['code', "is", sg_shot["code"]]], 
        ["sg_clip_name", "sg_scan_path", "sg_plate_resolution"]
    ) or []

    return shot_info

if __name__ == "__main__":
    project_name = "TEST_film"
    sequence_name = "EGR"
    shot_code = "EGR_0090"
    version_name = "EGR_0090_mp0_v005"
    task_name = "plate"
    status = "po"

    try:
        # 프로젝트 가져오기
        project = con.find_one("Project", [["name", "is", project_name]], ["id"])
        if not project:
            raise ValueError(f"프로젝트 '{project_name}'을(를) 찾을 수 없습니다.")

        # 샷 가져오기
        shot = con.find_one(
            "Shot",
            [["project", "is", project], ["code", "is", shot_code]],
            ["id"]
        )
        if not shot:
            raise ValueError(f"샷 '{shot_code}'을(를) 찾을 수 없습니다.")

        # 태스크 가져오기
        task = con.find_one(
            "Task",
            [["project", "is", project], ["entity", "is", shot], ["content", "is", task_name]],
            ["id"]
        )
        if not task:
            raise ValueError(f"태스크 '{task_name}'을(를) 찾을 수 없습니다.")

        # 새 버전 생성
        sg_version = con.create(
            "Version",
            {
                "project": project,
                "entity": shot,
                "code": version_name,
                "sg_task": task,
                "sg_status_list": status,
            }
        )
        print(f"새 버전 생성 완료: {sg_version}")
    except Exception as e:
        print(f"버전 생성 중 오류 발생: {e}")