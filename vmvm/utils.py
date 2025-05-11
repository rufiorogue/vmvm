import os
from pathlib import Path
from enum import StrEnum

def disk_image_format_by_name(filename: str) -> str:
    return 'qcow2' if 'qcow2' in filename else 'raw'

class SockType(StrEnum):
    SPICE = 'spice'
    QMP = 'qmp'

def get_unix_sock_path(sock_type: SockType, vm_name: str) -> str:
    dir = f'/run/user/{os.getuid()}/qemu/{vm_name}/'
    Path(dir).mkdir(parents=True,exist_ok=True)
    return dir + f'{sock_type}.sock'
