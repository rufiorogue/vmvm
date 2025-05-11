from vmvm.config_parser import parse_config

def test_default():
    o = parse_config(dict(name='foo'))

    assert o.disks == []
    assert o.name == "foo"
    assert o.cpus == 4
    assert o.ram == "4G"
    assert o.arch == "x86_64"
    assert o.machine == "q35"
    assert o.enable_efi == False
    assert o.enable_kvm == True
    assert o.cpu_model == "host"
    assert o.enable_boot_menu == False
    assert o.enable_secureboot == False
    assert o.enable_tpm == False
    assert o.disk_virtio_mode == "blk"
    assert o.usbdevices == []
    assert o.isoimages == []
    assert o.need_cd == False
    assert o.floppy == None
    assert o.share_dir_as_fat == None
    assert o.share_dir_as_floppy == None
    assert o.share_dir_as_fsd == None
    assert o.nic_model == "virtio"
    assert o.nic_forward_ports == []
    assert o.soundcard_model == "hda"
    assert o.gpu_model == "qxl-vga"
    assert o.display == "gtk"
    assert o.spice == "auto"
    assert o.control_socket == False


def test_prototype_linux_3daccel():
    o = parse_config(dict(name='foo',prototype='linux-x86_64-3daccel'))

    assert 'virtio-vga-gl' in o.gpu_model
    assert 'gl' in o.display
    assert 'none' in o.spice


def test_efi():
    o = parse_config(dict(name='foo',efi=True))

    assert o.enable_efi == True


def test_nokvm():
    o = parse_config(dict(name='foo',kvm=False))

    assert o.enable_kvm == False
    assert o.cpu_model == 'max'