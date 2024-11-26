
from vmvm.builder import VMOptions, RuntimeOptions, CmdBuilder
from pytest import fixture

@fixture
def vmoptions_default():

    return VMOptions(
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


def test_default(vmoptions_default):
    cmdline = CmdBuilder.boot_args(vmoptions_default, 'install')
    assert cmdline == ['-boot', 'once=d']
    cmdline = CmdBuilder.boot_args(vmoptions_default, 'run')
    assert cmdline == ['-boot', 'order=c']
    cmdline = CmdBuilder.cdrom_args(vmoptions_default, mount=False)
    assert cmdline == []
    cmdline = CmdBuilder.cdrom_args(vmoptions_default, mount=True)
    assert cmdline == []
    cmdline = CmdBuilder.common_args(vmoptions_default, RuntimeOptions(spice_port=123,tpm_socket="/tmp/my-socket"))
    assert cmdline == [
        '-name', 'foo',
        '-machine', 'q35',
        '-smp', '4',
        '-m', '4G',
        '-cpu', 'host',
        '-enable-kvm',
        '-device', 'qxl-vga',
        '-display', 'gtk',
        '-spice', 'port=123,disable-ticketing=on',
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


@fixture
def vmoptions_linux_1():

    return VMOptions(
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


def test_linux_1(vmoptions_linux_1):
    cmdline = CmdBuilder.common_args(vmoptions_linux_1, RuntimeOptions(spice_port=5900,tpm_socket=""))
    assert cmdline == [
        '-name', 'bar',
        '-machine', 'q35',
        '-smp', '8',
        '-m', '24G',
        '-cpu', 'host',
        '-enable-kvm',
        '-device', 'virtio-vga',
        '-display', 'none',
        '-spice', 'port=5900,disable-ticketing=on',
        '-device', 'virtio-serial-pci',
        '-device', 'virtserialport,chardev=spicechannel0,name=com.redhat.spice.0',
        '-chardev', 'spicevmc,id=spicechannel0,name=vdagent',
        '-blockdev', 'driver=qcow2,node-name=hd0,file.driver=file,file.filename=system.qcow2',
        '-device', 'virtio-blk-pci,id=virtblk0,num-queues=4,drive=hd0,bootindex=1',
        '-device', 'qemu-xhci',
        '-device', 'usb-tablet',
        '-netdev', 'user,id=net0,hostfwd=tcp::2222-:22',
        '-device', 'virtio-net-pci,netdev=net0',
        '-audiodev', 'pa,id=snd0',
        '-device', 'ich9-intel-hda',
        '-device', 'hda-output,audiodev=snd0',
    ]



@fixture
def vmoptions_cdrom():

    return VMOptions(
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


def test_cdrom(vmoptions_cdrom):
    cmdline = CmdBuilder.cdrom_args(vmoptions_cdrom, mount=True)
    assert cmdline == [
        '-blockdev', 'driver=file,read-only=on,node-name=isofile0,filename=foo.iso',
        '-blockdev', 'driver=raw,node-name=cdrom0,file=isofile0',
        '-device', 'ide-cd,bus=ide.0,drive=cdrom0,id=cddev0',
    ]


@fixture
def vmoptions_linux_3daccel():

    return VMOptions(
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


def test_linux_3daccel(vmoptions_linux_3daccel):
    cmdline = CmdBuilder.common_args(vmoptions_linux_3daccel, RuntimeOptions(spice_port=0,tpm_socket=""))
    assert cmdline == [
        '-name', 'bar',
        '-machine', 'q35',
        '-smp', '4',
        '-m', '4G',
        '-cpu', 'host',
        '-device', 'virtio-vga-gl',
        '-display', 'gtk',
        '-device', 'qemu-xhci',
        '-device', 'usb-tablet',
        '-nic', 'none',
    ]
