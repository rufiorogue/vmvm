from .builder import VMOptions
from .prototypes import prototype_config
import os
import subprocess
from typing import Any
import logging

class ConfigParserError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


def parse_config(conf: dict) -> VMOptions:

    running_hw_arch = subprocess.check_output(['uname', '-m']).decode().rstrip()

    consumed_opts = set()
    def consume(opt: str):
        consumed_opts.add(opt)

    def _wrap_scalar_as_list(x: Any | list[Any]) -> list[Any]:
        return x if type(x) == list else [x]

    def _fs_expand(path: str | list[str]) -> str | list[str]:
        """
        Applies common shell path expansions
        """
        if path is None:
            return None
        def _fs_expand_one(p: str):
            return p.replace('~',os.environ['HOME'])
        if type(path) == list:
            return list(map(_fs_expand_one,path))
        else:
            return _fs_expand_one(path)

    o_disks = _fs_expand(_wrap_scalar_as_list(conf.get('disk', conf.get('disks', [])))); consume('disk'); consume('disks')

    prototype_name = conf.get('prototype', f'default-{running_hw_arch}'); consume('prototype')
    if prototype_name == 'linux':
        prototype_name = f'linux-{running_hw_arch}'

    current_prototype = prototype_config[prototype_name]

    for k,v in current_prototype.items():
        # overwrite with preset value if not set in conf
        if k not in conf:
            conf[k] = v

    o_name = conf['name']; consume('name')
    o_cpus = conf['cpus']; consume('cpus')
    o_ram = conf['ram']; consume('ram')
    o_arch = conf['arch']; consume('arch')


    o_machine = conf.get('machine', {
        'i386':    'pc',  #  machine type corresponding to late 90s - early 2000s era
        'x86_64':  'q35',
        'aarch64': 'virt',
    }[o_arch] ); consume('machine')
    o_enable_efi = conf.get('efi',False); consume('efi')

    def is_supported_kvm_arch(vm_arch: str):
        match vm_arch:
            case 'i386':
                return running_hw_arch == 'x86_64'
            case _:
                return running_hw_arch == vm_arch
    o_enable_kvm = conf.get('kvm', is_supported_kvm_arch(o_arch) ); consume('kvm')

    o_cpu_model = conf.get('cpu_model', {
        'i386':    'qemu32',
        'x86_64':  'host',
        'aarch64': 'max',
    }[o_arch] ); consume('cpu_model')

    o_enable_boot_menu = conf.get('bootmenu',False); consume('bootmenu')
    o_enable_secureboot = conf.get('secureboot', False); consume('secureboot')
    o_enable_tpm = conf.get('tpm', False); consume('tpm')
    o_disk_virtio_mode = conf.get('disk_virtio', 'blk'); consume('disk_virtio')
    o_usbdevices =_wrap_scalar_as_list(conf.get('usb',[])); consume('usb')
    o_isoimages = _fs_expand(_wrap_scalar_as_list(conf.get('os_install',[]))); consume('os_install')
    o_need_cd = conf.get('need_cd', False); consume('need_cd')
    o_floppy = _fs_expand(conf.get('floppy', None)); consume('floppy')
    o_share_dir_as_fat = _fs_expand(conf.get('share_dir_as_fat', None)); consume('share_dir_as_fat')
    o_share_dir_as_floppy = _fs_expand(conf.get('share_dir_as_floppy', None)); consume('share_dir_as_floppy')
    o_share_dir_as_fsd = _fs_expand(conf.get('share_dir_as_fsd', None)); consume('share_dir_as_fsd')
    o_nic_model = conf.get('nic', 'none'); consume('nic')
    o_nic_forward_ports = conf.get('nic_forward_ports', []); consume('nic_forward_ports')
    o_soundcard_model = conf.get('sound', 'none'); consume('sound')

    o_gpu_model = conf.get('gpu', 'qxl-vga'); consume('gpu')
    o_display = conf.get('display','gtk'); consume('display')
    o_spice = conf.get('spice','auto'); consume('spice')
    gpu_is_accel = '-gl' in o_gpu_model
    if gpu_is_accel and o_display == 'none':
        raise ConfigParserError('display cannot be "none" if 3D acceleration is enabled')
    if gpu_is_accel and o_spice != 'none':
        raise ConfigParserError('cannot use SPICE if 3D acceleration is enabled')

    o_control_socket = conf.get('control_socket', False); consume('control_socket')

    found_invalid_option = False
    for opt_name in conf.keys():
        if opt_name not in consumed_opts:
            logging.error('Unrecognized option: "%s"',opt_name)
            found_invalid_option = True
    if found_invalid_option:
        raise ConfigParserError('the config file has unrecognized options')

    return VMOptions(
        name=o_name,
        cpus=o_cpus,
        ram=o_ram,
        arch=o_arch,
        cpu_model=o_cpu_model,
        machine=o_machine,
        enable_kvm=o_enable_kvm,
        enable_efi=o_enable_efi,
        enable_boot_menu=o_enable_boot_menu,
        enable_secureboot=o_enable_secureboot,
        enable_tpm=o_enable_tpm,
        disks=o_disks,
        disk_virtio_mode=o_disk_virtio_mode,
        isoimages=o_isoimages,
        need_cd=o_need_cd,
        usbdevices=o_usbdevices,
        share_dir_as_fat=o_share_dir_as_fat,
        share_dir_as_floppy=o_share_dir_as_floppy,
        share_dir_as_fsd=o_share_dir_as_fsd,
        floppy=o_floppy,
        nic_model=o_nic_model,
        nic_forward_ports=o_nic_forward_ports,
        soundcard_model=o_soundcard_model,
        gpu_model=o_gpu_model,
        display=o_display,
        spice=o_spice,
        control_socket=o_control_socket
    )

