# VMVM - QEMU wrapper and shell

The goal of this project is simplify the task of running QEMU for mere mortals. It is achieved by hiding complexity of QEMU command line under a simpler facade.

## Features

- Command-line interface to run QEMU and dependent processes from shell
- YAML file to configure the virtual machine
- Options for CPU, RAM, network, disk, EFI, SecureBoot, TPM for Windows 11, and more
- Auto-selection of machine type and default features based on architecture
- Support x86_64, i386 and aarch64 architectures

## Dependencies

- Python 3
- QEMU
- pyyaml

## Usage

To use VMVM, you need to create a YAML configuration file named `vmconfig.yml` in the directory from which you'll run the script.

Here is an example of a configuration file:

```yaml
name: windows10
cpus: 4
ram: 8G
disk: system.qcow2
os_install: 
    - Win10_21H2_English_x64.iso
```


After you've created your configuration file, you can perform various actions on your virtual machine. 

Action syntax:
```
<path_to_script> ACTION
```


| Action | Description |
| ------- | ----------- |
| `init`  | Initialize a new virtual machine. This will create a 100G `my_disk.qcow2` file (file name is derived from first entry in `disk` or `disks` config option. |
| `install` | Install an operating system on your virtual machine |
| `run` |  Run your virtual machine |

The only difference between `run` and `install` actions is that `install` will pass ISO images from `os_install` config option to QEMU, while `run` will ignore them.


## Configuration Options

| Option | Description | Example |
| ------ | ------------| ------ |
| `name` | Name of your virtual machine | `name: windows10`
| `cpus` | Number of CPUs for your virtual machine | `cpus: 4` |
| `ram`  | Amount of RAM for your virtual machine. You can specify this in gigabytes (G) or megabytes (M). | `ram: 8G`
| `arch` | (Optional) architecture: same as suffix part of `qemu-system-...`. Supported values are `i386`, `x86_64`, `aarch64` | arch: x86_64  |
| `machine` | (Optional) machine type:  see `qemu-system-<ARCH> -machine help`.  Default auto-selection: 'pc' for i386 arch, 'q35' for x86_64 arch, 'virt' for aarch64 | `machine: q35` |
| `efi` |  (Optional) enable EFI.  True=EFI, False=BIOS | `efi: False` |
| `secureboot` |  (Optional) enable EFI SecureBoot (`OVMF_CODE.secboot.fd`). Has no effect unless `efi` is set to True | `secureboot: False` |
| `tpm` | (Optional) software emulation of Trusted Platform Module 2.0. Requires [swtpm](https://www.qemu.org/docs/master/specs/tpm.html#the-qemu-tpm-emulator-device) to be installed | `tpm: False` |
| `bootmenu` |  (Optional) enable boot menu. Also consider [rules how boot disk is selected](#how-boot-disk-is-selected) |  `bootmenu: False` |
| `disk` (`disks`) | Disk image file. Can also be /dev/... file to pass through a host block device. (Optional) 'disks' is an alias for 'disk'. Both can be a single string or list of strings | `disk: system.qcow2`
| `disk_virtio` |  (Optional) for disk emulation, specify `blk` to use `virtio-blk`, `scsi` to use `virtio-scsi` or `none` to disable virtio and emulate IDE controller instead. Applicable only to image file based disks. `blk` theoretically yields best performance. `scsi` is best for large disk arrays. `none` for legacy OSes. See [note on performance](#a-note-on-disk_virtio)  | `disk_virtio: blk` |
| `os_install` | (Optional) will mount these images if action is `install`. Can be a single string or list of strings | `os_install: Windows10.iso`
| `usb` | (Optional) USB Passthrough. Can be a single device spec or list of specs. Device spec is `vendor:product`. USB device must be [accessible](#a-note-on-usb-passthrough) by running user | `usb: 1234:5678` |
| `share_dir_as_fsd` | (Optional) Share a host directory with [virtiofsd](https://virtio-fs.gitlab.io/index.html). Use with Linux guests. This method provides best performance as well as other useful virtualisation features. The shared directory can then be [mounted on guest](#mounting-virtiofsd-drive-on-guest) | `share_dir_as_fsd: shared`
| `share_dir_as_fat` | (Optional) Map a host directory as a [virtual FAT filesystem](https://www.qemu.org/docs/master/system/images.html#virtual-fat-disk-images)  on guest. *You should not use non-ASCII filenames or attempt to write to the FAT directory on the host system while accessing it with the guest system!* | `share_dir_as_fat: shared`
| `nic` | (Optional) allows to override or disable default network interface card selected by machine type.  `none` disables network card. `virtio` selects `virtio-net-pci` card. You can also specify exact model name (see `qemu-system-<ARCH> -device help` for list of network devices) | `nic: virtio` |
| `nic_forward_ports` | (Optional) Forward local port X to guest port Y. | [example](#nic-port-forwarding-example)
| `spice_port` | (Optional) port for the SPICE server. If not provided or set to `auto`, will find the next available port starting from 5900. | `spice_port: auto`

## Handy SMB server

As an alternative to `share_...` config options,  a docker compose is provided in subdirectory `smb` to spin up a SMB server, to be accessed from guest. Refer to respective [README](smb/README.md).


## A note on disk_virtio

`disk_virtio` = `blk` will create one controller for each disk on PCIe bus, so do not use `blk` if more than a few disks. Use `scsi` in such case.


## A note on USB Passthrough

QEMU user must be able to rw the device. One way to achieve this is to create a file `/etc/udev/rules.d/50-usbpassthrough.rules`

```udev
SUBSYSTEM=="usb", ATTR{idVendor}=="xxxx", ATTR{idProduct}=="xxxx", MODE="0666"
```

## NIC port forwarding example
```yaml
nic_forward_ports:
    - host: 2222
      guest: 22
```
then on the host you can do:
```
$ ssh localhost -p 2222
```

## Mounting `virtiofsd` drive on guest
You can mount the directory on the guest as follows:
```
# mount -t 9p -o trans=virtio,version=9p2000.L hostshare /mnt/share
```

## How boot disk is selected

If menu is disabled, the boot disk is selected depending on ACTION:
-  if ACTION is `install`, first boot - from CD, on reboot - from hard disk
-  if ACTION is `run`, always boot from first hard disk in the `disks` list

## Contributing

If you would like to contribute to this project, please feel free to submit a pull request or open an issue on GitHub.

## License

This project is open source and available under the [GPLv3 License](LICENSE).
