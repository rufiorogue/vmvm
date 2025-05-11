import logging, yaml, os, socket, argparse
from logging import info,error

from .config_parser import parse_config
from .builder import CmdBuilder, RuntimeOptions, CommonArgsBuildResult
from .exec import exec_with_trace
from .utils import disk_image_format_by_name, get_unix_sock_path, SockType
from .tpm_manager import TPMManager
from .hw_caps import check_has_topoext

SPICE_PORT_BASE=5900


def is_port_free(port: int) -> bool:
    s = socket.socket()
    try:
        s.bind(('localhost',port))
        return True
    except:
        pass
    return False

def find_next_free_port(port: int) -> int:
    while not is_port_free(port):
        port += 1
    return port


class App:


    def __init__(self, conf_dir: str):
        self.tpm_manager = None
        os.chdir(conf_dir)
        conf = yaml.safe_load(open('vmconfig.yml', 'r'))
        self._options = parse_config(conf)
        logging.debug('**** options: ****')
        logging.debug(repr(self._options))
        logging.debug('******************')

    def _start_tpm(self):
        if self._options.enable_tpm:
            info('starting software TPM daemon')
            self.tpm_manager = TPMManager(self._options.name)
            self.tpm_manager.run()

    def _shutdown_tpm(self):
        if self._options.enable_tpm:
            info('shutting down software TPM daemon')
            self.tpm_manager.shutdown()


    def act_init(self):
        info('action: initializing vm')

        if len(self._options.disks):
            first_disk = self._options.disks[0]
            if os.path.exists(first_disk):
                error('disk already exists, not overwriting: %s', first_disk)
                return
            else:
                img_format = disk_image_format_by_name(first_disk)
                info('creating empty disk %s with size %s and format %s', first_disk, '100G', img_format.upper())
                exec_with_trace('qemu-img', ['create', '-f', img_format, first_disk, '100G'])
        else:
            error('no disks configured?')

    def act_install(self):
        self._start_tpm()
        info('action: installing operating system inside vm')
        runtime_options = RuntimeOptions(
            spice_port=find_next_free_port(SPICE_PORT_BASE),
            tpm_socket=self.tpm_manager.sock if self.tpm_manager else None,
            has_cpu_topoext=check_has_topoext()
            )
        cmd_builder = CmdBuilder()
        common_args_build_result: CommonArgsBuildResult = cmd_builder.common_args(self._options,runtime_options)
        for pre_command in common_args_build_result.pre_commands:
            exec_with_trace(pre_command.exe, pre_command.args)
        args = common_args_build_result.args + cmd_builder.boot_args(self._options,mode='install') + cmd_builder.cdrom_args(self._options,mount=True)
        exec_with_trace(f'qemu-system-{self._options.qemu_binary}', args)
        self._shutdown_tpm()


    def act_run(self):
        self._start_tpm()
        info('action: running vm')
        runtime_options = RuntimeOptions(
            spice_port=find_next_free_port(SPICE_PORT_BASE),
            tpm_socket=self.tpm_manager.sock if self.tpm_manager else None,
            has_cpu_topoext=check_has_topoext()
            )
        cmd_builder = CmdBuilder()
        common_args_build_result: CommonArgsBuildResult = cmd_builder.common_args(self._options,runtime_options)
        for pre_command in common_args_build_result.pre_commands:
            exec_with_trace(pre_command.exe, pre_command.args)
        args = common_args_build_result.args + cmd_builder.boot_args(self._options,mode='run') + cmd_builder.cdrom_args(self._options,mount=False)
        exec_with_trace(f'qemu-system-{self._options.qemu_binary}', args)
        self._shutdown_tpm()

    def act_console(self):
        import asyncio
        import qemu.qmp
        import readline
        from rich import print as rprint
        import re

        async def console_main():
            qmp = qemu.qmp.QMPClient(self._options.name)
            socket_path = get_unix_sock_path(SockType.QMP, self._options.name)
            await qmp.connect(socket_path)
            print(f'Welcome to the QMP console. You are controlling "{self._options.name}"')

            async def qmp_try(cmd: str):
                tokens = cmd.split()
                if len(tokens) > 1:
                    # assume 1st token is command, the rest are arguments
                    cmd_exec = tokens[0]
                    def parse_arg_val(arg_val: str):
                        if re.match(r'^\[\w+[,\w]*\]$', arg_val):
                            values = arg_val.replace('[','').replace(']','').split(',')
                            return values
                        else:
                            return arg_val
                    cmd_args =  { arg.split('=')[0]: parse_arg_val(arg.split('=')[1]) for arg in tokens[1:] }
                else:
                    cmd_exec = cmd
                    cmd_args = None
                try:
                    res = await qmp.execute(cmd_exec, cmd_args)
                    rprint(res)
                except Exception as e:
                    print(e)
            while True:
                cmd = input('> ')
                match cmd:
                    case 'q' | 'quit':
                        break
                    case 'h' | 'help':
                        res = await qmp.execute('query-commands')
                        print('\n'.join(sorted([x['name'] for x in res])))

                    case _:
                        await qmp_try(cmd)

            await qmp.disconnect()

        asyncio.run(console_main())


USAGE= '''

    vmvm <ACTION> [CONF_DIR]

ACTION = init | install | run

    init          create an image file for the first HDD in the config (if not exist)
    install       boot from 'os_install' device to install operating system
    run           boot from first HDD
    console       open an interactive QMP shell (control_socket option must be enabled)

CONF_DIR
    is a directory containing vmconfig.yml. Default is CWD.

Example:
    vmvm install

Configuration Options:
    name                Name of the virtual machine (str, required)
    prototype           Specify a hint to the installed operating system personality (linux, w10, w11, wxp, w2k, w98)
    cpus                Number of CPUs (uint)
    ram                 Amount of RAM (with suffix such as M or G)
    arch                Architecture (i386, x86_64, aarch64)
    efi                 Enable EFI (True/False)
    secureboot          Enable EFI SecureBoot (True/False)
    tpm                 Enable software TPM emulation (True/False)
    bootmenu            Enable boot menu (True/False)
    floppy              Floppy image file (path)
    disk (disks)        Disk image file or list (path or list of paths, required)
    disk_virtio         Disk emulation (blk, scsi, none)
    os_install          mount ISO images if ACTION=='install' (path or list of paths)
    need_cd             always mount ISO images, even if ACTION is not 'install' (True/False)
    usb                 USB Passthrough (pair or list of pairs like vendor:product)
    share_dir_as_fsd    Share a host directory with virtiofsd (path)
    share_dir_as_fat    Map a host directory as a virtual FAT filesystem (path)
    share_dir_as_floppy Map a host directory as a virtual floppy (path)
    nic                 Network interface card (none, virtio, or <specific model>)
    nic_forward_ports   Forward local port to guest port (scalar or list of dicts like "host: 2222, guest: 22")
    gpu                 GPU model (see qemu-system-<ARCH> -device help and "Display devices" section)
    display             QEMU UI backend (see qemu-system-<ARCH> -display help)
    sound               Sound card type (hda, ac97, sb16, none)
    spice               SPICE server config (unix, auto, <port number>, none)
    control_socket      Enable QMP control socket (True/False)

'''


def main():
    parser = argparse.ArgumentParser(prog='vmvm', description='User friendly QEMU frontend', usage=USAGE)
    parser.add_argument('cmd', choices=['init','install','run','console'])
    parser.add_argument('dir_name', nargs='?', default=os.getcwd())
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s  %(levelname)s  %(message)s', level=logging.DEBUG if args.cmd != 'console' else logging.WARNING)


    app = App(args.dir_name)
    getattr(app,'act_'+args.cmd)()


if __name__ == '__main__':
    main()
