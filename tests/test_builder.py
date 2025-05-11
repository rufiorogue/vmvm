
from vmvm.builder import VMOptions, RuntimeOptions, CmdBuilder
import pytest


def is_sublist(needle, haystack):
    """ check if 'needle' list is exact sublist of 'haystack' list """
    return str(needle)[1:-1] in str(haystack)[1:-1]



def test_default():

    vmoptions_default = VMOptions(
        disks = [],
        name = "foo",
        cpus = 4,
        ram = "4G",
        arch = "x86_64",
        machine = "q35",
        enable_efi = False,
        enable_kvm = True,
        cpu_model = "host",
        enable_boot_menu = False,
        enable_secureboot = False,
        enable_tpm = False,
        disk_virtio_mode = "blk",
        usbdevices = [],
        pcidevices = [],
        isoimages = [],
        need_cd = False,
        floppy = None,
        share_dir_as_fat = None,
        share_dir_as_floppy = None,
        share_dir_as_fsd = None,
        nic_model = "virtio",
        nic_forward_ports = [],
        soundcard_model = "hda",
        gpu_model = "qxl-vga",
        display = "gtk",
        spice = "auto",
        control_socket = False,
    )

    b = CmdBuilder()
    cmdline = b.boot_args(vmoptions_default, 'install')
    assert cmdline == ['-boot', 'once=d']
    cmdline = b.boot_args(vmoptions_default, 'run')
    assert cmdline == ['-boot', 'order=c']
    cmdline = b.cdrom_args(vmoptions_default, mount=False)
    assert cmdline == []
    cmdline = b.cdrom_args(vmoptions_default, mount=True)
    assert cmdline == []
    cmdline = b.common_args(vmoptions_default, RuntimeOptions(spice_port=123,tpm_socket="/tmp/my-socket")).args
    assert cmdline == [
        '-name', 'foo',
        '-machine', 'q35',
        '-smp', '4',
        '-m', '4G',
        '-cpu', 'host',
        '-enable-kvm',
        '-device', 'qxl-vga',
        '-display', 'gtk',
        '-spice', 'port=123,addr=127.0.0.1,disable-ticketing=on',
        '-device', 'virtio-serial-pci',
        '-device', 'virtserialport,chardev=spicechannel0,name=com.redhat.spice.0',
        '-chardev', 'spicevmc,id=spicechannel0,name=vdagent',
        '-device', 'qemu-xhci',
        '-device', 'usb-tablet',
        '-netdev', 'user,id=net0',
        '-device', 'virtio-net-pci,netdev=net0',
        '-audiodev', 'pa,id=snd0',
        '-device', 'ich9-intel-hda',
        '-device', 'hda-output,audiodev=snd0'
        ]


vmoptions_linux_1 = VMOptions(
    disks = [ "system.qcow2"],
    name = "bar",
    cpus = 8,
    ram = "24G",
    arch = "x86_64",
    machine = "q35",
    enable_efi = False,
    enable_kvm = True,
    cpu_model = "host",
    enable_boot_menu = False,
    enable_secureboot = False,
    enable_tpm = False,
    disk_virtio_mode = "blk",
    usbdevices = [],
    pcidevices = [],
    isoimages = ["anything here"],
    need_cd = False,
    floppy = None,
    share_dir_as_fat = None,
    share_dir_as_floppy = None,
    share_dir_as_fsd = None,
    nic_model = "virtio",
    nic_forward_ports =  [{
            "host": 2222,
            "guest": 22,
        }],
    soundcard_model = "hda",
    gpu_model = "virtio-vga",
    display = "none",
    spice = "auto",
    control_socket = False,
)


def test_linux_1():
    b = CmdBuilder()
    cmdline = b.common_args(vmoptions_linux_1, RuntimeOptions(spice_port=5900,tpm_socket="")).args
    assert cmdline == [
        '-name', 'bar',
        '-machine', 'q35',
        '-smp', '8',
        '-m', '24G',
        '-cpu', 'host',
        '-enable-kvm',
        '-device', 'virtio-vga',
        '-display', 'none',
        '-spice', 'port=5900,addr=127.0.0.1,disable-ticketing=on',
        '-device', 'virtio-serial-pci',
        '-device', 'virtserialport,chardev=spicechannel0,name=com.redhat.spice.0',
        '-chardev', 'spicevmc,id=spicechannel0,name=vdagent',
        '-blockdev', 'driver=qcow2,node-name=hd0,file.driver=file,file.filename=system.qcow2,discard=unmap,detect-zeroes=unmap',
        '-device', 'virtio-blk-pci,id=virtblk0,num-queues=4,drive=hd0,bootindex=1',
        '-device', 'qemu-xhci',
        '-device', 'usb-tablet',
        '-netdev', 'user,id=net0,hostfwd=tcp::2222-:22',
        '-device', 'virtio-net-pci,netdev=net0',
        '-audiodev', 'pa,id=snd0',
        '-device', 'ich9-intel-hda',
        '-device', 'hda-output,audiodev=snd0',
    ]


def make_vmoptions_linux_efi_nosecboot():
    options = vmoptions_linux_1
    options.enable_efi = True
    options.enable_secureboot = False
    return options

def make_vmoptions_linux_efi_secboot():
    options = vmoptions_linux_1
    options.enable_efi = True
    options.enable_secureboot = True
    return options

def test_linux_efi_edk2_not_installed():
    b = CmdBuilder(listdir_fn=lambda _: [], pathexists_fn=lambda _: False)
    with pytest.raises(FileNotFoundError):
        b.common_args(make_vmoptions_linux_efi_nosecboot(), RuntimeOptions(spice_port=5900,tpm_socket="")).args


def test_linux_efi():

    def test_variant(efi_dir_contents, options, expectation):
        my_listdir = lambda _: efi_dir_contents
        def my_path_exists(p):
            if '/usr/share/edk2/x64' in p:
                p = p.replace('/usr/share/edk2/x64/','')
                return p in efi_dir_contents
            return False
        b = CmdBuilder(listdir_fn=my_listdir, pathexists_fn=my_path_exists)
        cmdline = b.common_args(options, RuntimeOptions(spice_port=5900,tpm_socket="")).args
        assert is_sublist(expectation, cmdline)


    test_variant(
            [
                'OVMF_CODE.fd', 'OVMF_CODE.secboot.fd', 'OVMF_VARS.fd'
            ],
            make_vmoptions_linux_efi_nosecboot(),
            [
                '-drive', 'if=pflash,format=raw,readonly=on,file=/usr/share/edk2/x64/OVMF_CODE.fd',
                '-drive', 'if=pflash,format=raw,file=./OVMF_VARS.fd',
            ])

    test_variant(
            [
                'OVMF_CODE.fd', 'OVMF_CODE.secboot.fd', 'OVMF_VARS.fd'
            ],
            make_vmoptions_linux_efi_secboot(),
            [
                '-drive', 'if=pflash,format=raw,readonly=on,file=/usr/share/edk2/x64/OVMF_CODE.secboot.fd',
                '-drive', 'if=pflash,format=raw,file=./OVMF_VARS.fd',
            ])

    test_variant(
            [
                'MICROVM.4m.fd', 'OVMF.4m.fd', 'OVMF_CODE.4m.fd', 'OVMF_CODE.secboot.4m.fd', 'OVMF_VARS.4m.fd'
            ],
            make_vmoptions_linux_efi_nosecboot(),
            [
                '-drive', 'if=pflash,format=raw,readonly=on,file=/usr/share/edk2/x64/OVMF_CODE.4m.fd',
                '-drive', 'if=pflash,format=raw,file=./OVMF_VARS.4m.fd',
            ])

 
    test_variant(
            [
                'MICROVM.4m.fd', 'QEMU.4m.fd', 'QEMU_CODE.4m.fd', 'QEMU_CODE.secboot.4m.fd', 'QEMU_VARS.4m.fd'
            ],
            make_vmoptions_linux_efi_nosecboot(),
            [
                '-drive', 'if=pflash,format=raw,readonly=on,file=/usr/share/edk2/x64/QEMU_CODE.4m.fd',
                '-drive', 'if=pflash,format=raw,file=./QEMU_VARS.4m.fd',
            ])



def test_cdrom():
    vmoptions_cdrom = VMOptions(
        disks = [],
        name = "bar",
        cpus = 4,
        ram = "4G",
        arch = "x86_64",
        machine = "q35",
        enable_efi = False,
        enable_kvm = True,
        cpu_model = "host",
        enable_boot_menu = False,
        enable_secureboot = False,
        enable_tpm = False,
        disk_virtio_mode = "blk",
        usbdevices = [],
        pcidevices = [],
        isoimages = ["foo.iso"],
        need_cd = False,
        floppy = None,
        share_dir_as_fat = None,
        share_dir_as_floppy = None,
        share_dir_as_fsd = None,
        nic_model = "virtio",
        nic_forward_ports = [],
        soundcard_model = "hda",
        gpu_model = "qxl-vga",
        display = "gtk",
        spice = "auto",
        control_socket = False,
    )

    b = CmdBuilder()
    cmdline = b.cdrom_args(vmoptions_cdrom, mount=True)
    assert cmdline == [
        '-blockdev', 'driver=file,read-only=on,node-name=isofile0,filename=foo.iso',
        '-blockdev', 'driver=raw,node-name=cdrom0,file=isofile0',
        '-device', 'ide-cd,bus=ide.0,drive=cdrom0,id=cddev0',
    ]



def test_linux_3daccel():
    vmoptions_linux_3daccel = VMOptions(
        disks = [],
        name = "bar",
        cpus = 4,
        ram = "4G",
        arch = "x86_64",
        machine = "q35",
        enable_efi = False,
        enable_kvm = False,
        cpu_model = "host",
        enable_boot_menu = False,
        enable_secureboot = False,
        enable_tpm = False,
        disk_virtio_mode = "blk",
        usbdevices = [],
        pcidevices = [],
        isoimages = ["foo.iso"],
        need_cd = False,
        floppy = None,
        share_dir_as_fat = None,
        share_dir_as_floppy = None,
        share_dir_as_fsd = None,
        nic_model = "none",
        nic_forward_ports = [],
        soundcard_model = "none",
        gpu_model = "virtio-vga-gl",
        display = "gtk",
        spice = "none",
        control_socket = False,
    )
    b = CmdBuilder()
    cmdline = b.common_args(vmoptions_linux_3daccel, RuntimeOptions(spice_port=0,tpm_socket="")).args
    assert is_sublist([
        '-device', 'virtio-vga-gl',
        ], cmdline)
