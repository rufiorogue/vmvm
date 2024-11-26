import os

DEFAULT_CPUS = min(4, os.cpu_count())
DEFAULT_RAM = "4G"
DEFAULT_RAM_WINDOWS = "8G"

prototype_config = {}
prototype_config ['default-x86_64'] = {
  'arch': 'x86_64',
  'cpus': DEFAULT_CPUS,
  'ram': DEFAULT_RAM,
  'gpu': 'qxl-vga',
  'nic': 'virtio',
  'disk_virtio': 'blk',
  'sound': 'hda',
}

prototype_config ['default-aarch64'] = {
  'arch': 'aarch64',
  'cpus': DEFAULT_CPUS,
  'ram': DEFAULT_RAM,
  'gpu': 'virtio-gpu-pci',
  'nic': 'e1000',
  'disk_virtio': 'scsi',
  'sound': 'hda',
  'efi': True,
}

prototype_config ['linux-x86_64'] = prototype_config ['default-x86_64'].copy()
prototype_config ['linux-x86_64']['gpu'] = 'virtio-vga'

prototype_config ['linux-x86_64-3daccel'] = prototype_config ['default-x86_64'].copy()
prototype_config ['linux-x86_64-3daccel']['gpu'] = 'virtio-vga-gl,hostmem=8G'
prototype_config ['linux-x86_64-3daccel']['display'] = 'gtk,gl=on'
prototype_config ['linux-x86_64-3daccel']['spice'] = 'none'

prototype_config ['linux-aarch64'] = prototype_config ['default-aarch64'].copy()

prototype_config ['linux'] = prototype_config ['linux-x86_64'].copy()

prototype_config ['w10'] = prototype_config ['default-x86_64'].copy()
prototype_config ['w10']['ram'] = DEFAULT_RAM_WINDOWS
prototype_config ['w10']['gpu'] = 'qxl-vga'


prototype_config ['w11'] = prototype_config ['default-x86_64'].copy()
prototype_config ['w11']['ram'] = DEFAULT_RAM_WINDOWS
prototype_config ['w11']['gpu'] = 'qxl-vga'
prototype_config ['w11']['efi'] = True
prototype_config ['w11']['tpm'] = True
prototype_config ['w11']['secureboot'] = True



# buckle up Dorothy, turning on the time machine


prototype_config ['wxp'] = {
  'arch': 'i386',
  'cpus': 4,
  'ram': '512M',
  'gpu': 'qxl-vga',
  'nic': 'rtl8139',
  'disk_virtio': None,
  'sound': 'ac97',
}

prototype_config ['w2k'] = {
  'arch': 'i386',
  'cpus': 1,
  'ram': '128M',
  'gpu': 'cirrus-vga',
  'nic': 'rtl8139',
  'disk_virtio': None,
  'sound': 'ac97',
}

#TODO: Windows 98 wouldn't work straight away in QEMU, requires patcher9x.

prototype_config ['w9x'] = {
  'arch': 'i386',
  'cpus': 1,
  'ram': '128M',
  'gpu': 'cirrus-vga',
  'nic': 'rtl8139',
  'disk_virtio': None,
  'sound': 'ac97',
}
