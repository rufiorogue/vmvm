import os
import os.path
from pathlib import Path
import logging
import json
from .utils import disk_image_format_by_name, get_unix_sock_path, SockType

from dataclasses import dataclass

@dataclass
class VMOptions:
    name: str
    cpus: int
    ram: str
    arch: str
    cpu_model: str
    machine: str
    enable_kvm: bool
    enable_efi: bool
    enable_boot_menu: bool
    enable_secureboot: bool
    enable_tpm: bool
    disks: list[str]
    disk_virtio_mode: str
    isoimages: list[str]
    need_cd: bool
    usbdevices: list
    share_dir_as_fat: str
    share_dir_as_floppy: str
    share_dir_as_fsd: str
    floppy: str
    nic_model: str
    nic_forward_ports: list
    soundcard_model: str
    gpu_model: str
    display: str
    spice: str
    control_socket: bool

    def __repr__(self) -> str:
        return json.dumps(dict(self.__dict__.items()),indent=4)

    @property
    def qemu_binary(self):
        return {
        'i386':    'x86_64', # i386 uses qemu-system-x86_64 but sets -cpu qemu32
        'x86_64':  'x86_64',
        'aarch64': 'aarch64',
        }[self.arch]

    @property
    def edk2_subdir(self):
        return {
        'i386':    None,
        'x86_64':  'x64',
        'aarch64': 'aarch64',
        }[self.arch]


@dataclass
class RuntimeOptions:
    spice_port: int
    tpm_socket: str

@dataclass
class ExecCommand:
    exe: str
    args: list[str]

@dataclass
class CommonArgsBuildResult:
    args: list[str]
    pre_commands: list[ExecCommand]

class CmdBuilder:
    def __init__(self, listdir_fn=os.listdir, pathexists_fn=os.path.exists):
        self._listdir = listdir_fn
        self._path_exists = pathexists_fn

    def common_args(self, o: VMOptions, uo: RuntimeOptions) -> CommonArgsBuildResult:


        args = [
            '-name', o.name,
            '-machine', o.machine,
            '-smp', str(o.cpus),
            '-m', o.ram,
            '-cpu', o.cpu_model,

            #'-balloon', 'virtio',
            #'-localtime',
        ]

        pre_commands: list[ExecCommand] = []

        if o.enable_kvm:
            args += [ '-enable-kvm' ]

        if o.gpu_model and o.gpu_model != 'none':
            args += [ '-device', o.gpu_model ]

        # GUI:
        args += [ f'-display', o.display ]

        # SPICE:
        if o.spice != 'none':
            if o.spice == 'unix':
                spice_unix_sock_path = get_unix_sock_path(sock_type=SockType.SPICE, vm_name=o.name)
                logging.info('SPICE server running on unix://%s', spice_unix_sock_path)

                args += [
                    '-spice', f'unix=on,addr={spice_unix_sock_path},disable-ticketing=on',
                ]
            else:
                spice_port = o.spice
                if spice_port == 'auto':
                    spice_port = uo.spice_port
                logging.info('SPICE server running on tcp://localhost:%s', spice_port)

                args += [
                    '-spice', f'port={spice_port},addr=127.0.0.1,disable-ticketing=on',
                ]
            # common SPICE args
            args += [
                '-device', 'virtio-serial-pci',
                '-device', 'virtserialport,chardev=spicechannel0,name=com.redhat.spice.0',
                '-chardev', 'spicevmc,id=spicechannel0,name=vdagent',
            ]

        # QMP
        if o.control_socket:
            qmp_unix_sock_path = get_unix_sock_path(sock_type=SockType.QMP,vm_name=o.name)
            args += [ '-qmp', f'unix:{qmp_unix_sock_path},server,nowait', ]
            logging.info('control socket available on unix://%s', qmp_unix_sock_path)

        # EFI
        if o.enable_efi:
            edk2_dir = f'/usr/share/edk2/{o.edk2_subdir}'

            # logic to locate edk2 files
            edk2_dir_files = self._listdir(edk2_dir)
            code_fd = None
            vars_fd_src = None
            for filename in edk2_dir_files:
                if code_fd is None:
                    if 'CODE' in filename:
                        if o.enable_secureboot:
                            if 'secboot' in filename:
                                code_fd = edk2_dir + '/' + filename
                        else:
                            if 'secboot' not in filename:
                                code_fd = edk2_dir + '/' + filename
                if vars_fd_src is None:
                    if 'VARS' in filename:
                        vars_fd_src = edk2_dir + '/' + filename

            vars_fd_local =  f'./{os.path.basename(vars_fd_src)}' if vars_fd_src else None

            if self._path_exists(code_fd) and self._path_exists(vars_fd_src):

                if not self._path_exists(vars_fd_local):
                    logging.info(f'{vars_fd_local} file does not exist in VM directory, copying from system')
                    pre_commands.append(ExecCommand(exe='cp',args=[vars_fd_src, '.']))

                args += [
                    '-drive', f'if=pflash,format=raw,readonly=on,file={code_fd}',
                    '-drive', f'if=pflash,format=raw,file={vars_fd_local}',
                ]

            else:
                #error('edk2 files not found. Please install edk2-ovmf package.')
                package_name_suffix = {
                    'x86_64':  'ovmf',
                    'aarch64': 'aarch64',
                }[o.arch]
                raise FileNotFoundError(f'edk2 files not found. Please install edk2-{package_name_suffix} package.')


        # TPM
        if o.enable_tpm:
            args += [
                '-chardev', f'socket,id=chrtpm,path={uo.tpm_socket}', '-tpmdev', 'emulator,id=tpm0,chardev=chrtpm', '-device', 'tpm-tis,tpmdev=tpm0',
            ]


        def generate_blockdev_desc(idx: int, filename: str,disk_virtio_mode: str) -> list[str]:
            trim_options = 'discard=unmap,detect-zeroes=unmap'
            if '/dev' in filename:
                d = [
                    '-blockdev', f'driver=raw,node-name=hosthd{idx},file.driver=host_device,file.filename={filename},{trim_options}',
                ]
            else:
                img_format_driver = disk_image_format_by_name(filename)
                d = [
                   '-blockdev', f'driver={img_format_driver},node-name=hd{idx},file.driver=file,file.filename={filename},{trim_options}',
                ]

                if disk_virtio_mode == 'scsi':
                    d += [
                        '-device', f'scsi-hd,drive=hd{idx},bootindex={idx+1}',
                    ]
                elif disk_virtio_mode == 'blk':
                    d += [
                        '-device', f'virtio-blk-pci,id=virtblk{idx},num-queues=4,drive=hd{idx},bootindex={idx+1}',
                        ]
                else:
                    d += [
                        '-device', f'ide-hd,drive=hd{idx},bootindex={idx+1}',
                    ]
            return d

        # disk images
        if o.disk_virtio_mode == 'scsi':
            args += [ '-device', 'virtio-scsi-pci,id=scsi0,num_queues=4' ]
        for idx,disk in enumerate(o.disks):
            args += generate_blockdev_desc(idx, disk, o.disk_virtio_mode)

        # floppy image
        if o.floppy is not None:
            args += [
                '-blockdev', f'driver=file,node-name=floppy0,filename={o.floppy}',
                '-device', 'floppy,drive=floppy0',
            ]

        # share directory as virtual FAT hard disk
        if o.share_dir_as_fat is not None:
            args += [
                '-blockdev', f'driver=vvfat,node-name=fs_fat,dir={o.share_dir_as_fat},read-only=on,rw=off',
                '-device', 'usb-storage,drive=fs_fat',

                #'-hda', f'fat:ro:{self.share_dir_as_fat}',

                #'-drive', f'file=fat:rw:{self.share_dir_as_fat},format=raw,media=disk',
            ]

        # share directory as virtual floppy
        if o.share_dir_as_floppy is not None:
            args += [
                '-blockdev', f'driver=vvfat,node-name=fs_floppy,dir={o.share_dir_as_floppy},read-only=off,rw=on',
                '-device', 'floppy,drive=fs_floppy',
            ]

        # virtiofsd share
        if o.share_dir_as_fsd is not None:
            dir_abs = os.path.abspath(o.share_dir_as_fsd)
            args += [
                '-fsdev', f'local,security_model=passthrough,id=fsdev0,path={dir_abs}',
                '-device', 'virtio-9p-pci,fsdev=fsdev0,mount_tag=hostshare',
            ]

        # emulated USB devices
        if o.machine == 'pc':
            args += [
                '-usb',                        # add a UHCI controller (USB 1.1). Bus name usb-bus.0
                '-device', 'usb-ehci,id=ehci', # add a EHCI controller (USB 2.0). Bus name ehci.0
                '-device', 'usb-tablet,bus=ehci.0',
                #'-device', 'usb-mouse,bus=usb-bus.0',
                #'-device', 'usb-kbd,bus=usb-bus.0',
            ]
        else:
            args += [
                '-device', 'qemu-xhci',
                '-device', 'usb-tablet',
            ]

        # passthrough USB devices
        for usb_dev in o.usbdevices:
            vendor_id,product_id = usb_dev.split(':')
            args += [ '-device', f'usb-host,vendorid=0x{vendor_id},productid=0x{product_id}' ]

        # net
        # https://wiki.qemu.org/Documentation/Networking

        if o.nic_model != 'none':
            if len(o.nic_forward_ports) > 0:
                hostfwd_list = list(map(lambda bind_spec: f"hostfwd=tcp::{bind_spec['host']}-:{bind_spec['guest']}" , o.nic_forward_ports))
                hostfwd = ','+','.join(hostfwd_list)
            else:
                hostfwd = ''
            nic_model = o.nic_model
            nic_model = 'virtio-net-pci' if nic_model == 'virtio' else nic_model
            args += ['-netdev', f'user,id=net0{hostfwd}', '-device', f'{nic_model},netdev=net0' ]
        else:
            args += [ '-nic', 'none' ]

        # Sound Card (and PC speaker)
        match o.soundcard_model:
            case 'spk':
                args += [ '-audiodev', 'pa,id=spk0', '-machine', 'pcspk-audiodev=spk0', ]
            case 'sb16':
                args += [ '-audiodev', 'pa,id=snd0', '-device', 'sb16,audiodev=snd0', ]
            case 'ac97':
                args += [ '-audiodev', 'pa,id=snd0', '-device', 'ac97,audiodev=snd0', ]
            case 'hda':
                args += [ '-audiodev', 'pa,id=snd0', '-device', 'ich9-intel-hda', '-device', 'hda-output,audiodev=snd0', ]


        if o.display == 'none':
            logging.info(f"No GUI is configured, use SPICE{' or QMP socket' if o.control_socket else ''} to control")

        return CommonArgsBuildResult(args=args, pre_commands=pre_commands)

    def boot_args(self, o: VMOptions, mode: str) -> list[str]:
        args = []
        if o.enable_boot_menu:
            args = [ '-boot', 'menu=on', ]
        else:
            if mode == 'install':
                # boot from CD-ROM first, switch back to default order after reboot
                args = [ '-boot', 'once=d', ]
            elif mode == 'run':
                args = [ '-boot', 'order=c', ]
        return args

    def cdrom_args(self, o: VMOptions, mount: bool) -> list[str]:
        args = []
        def num_ide_slots() -> int:
            match o.machine:
                case 'pc': return 2
                case 'q35': return 6
                case _: return 0
        ide_bus_free_slots = num_ide_slots() if o.disk_virtio_mode != 'none' else max(0, num_ide_slots() - len(o.disks))
        added_scsi_adapter  = False
        if (mount or o.need_cd) and o.isoimages:
            for idx, isofile in enumerate(o.isoimages):
                isofile = isofile.replace(',', ',,') # double every ',' to escape it
                args += [
                    '-blockdev', f'driver=file,read-only=on,node-name=isofile{idx},filename={isofile}',
                    '-blockdev', f'driver=raw,node-name=cdrom{idx},file=isofile{idx}',
                ]
                if idx < ide_bus_free_slots:
                    args += [ '-device', f'ide-cd,bus=ide.{idx+num_ide_slots()-ide_bus_free_slots},drive=cdrom{idx},id=cddev{idx}', ]
                else: # To add additional CD-ROMs use SCSI adapter
                    if not added_scsi_adapter:
                        args += [ '-device', 'usb-bot,id=usbbot' ]
                        added_scsi_adapter = True
                    args += [ '-device', f'scsi-cd,bus=usbbot.0,lun={idx-ide_bus_free_slots},drive=cdrom{idx},id=cddev{idx}', ]
        else:
            #TODO: can we change name of default Q35 IDE CD-ROM device (ide2-cd0)?
            args += [
            ]

        return args
