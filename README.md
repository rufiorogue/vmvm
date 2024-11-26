# VMVM - a user friendly QEMU frontend

Running QEMU is hard for mere mortals. It has a lot of options and even simplest tasks require passing a lot of them to fully define the virtual environment. With this app a lot of complexity can be hidden away under a simple facade of a small config file.

## Features

- Command-line interface to run QEMU and dependent processes from shell
- YAML file to configure the virtual machine
- Options for CPU, RAM, network, disk, EFI, SecureBoot, TPM for Windows 11, and more
- Auto-selection of machine type and default features based on architecture
- Support x86_64, i386 and aarch64 architectures

## Dependencies

- QEMU
- Python 3
- python-yaml

## Installation

This project has been wrapped into a Python package using `poetry` and includes a PKGBUILD file for AUR compatibility.

### For Python Package
Run `poetry build -v -n` to build the Python package.

### For Arch Linux Package
Run `makepkg -sri` to build and install the Arch Linux package.

### Alternative Installation Method
Install the Python package directly from the repository using pip:
```bash
pip install git+https://github.com/roovio/vmvm
```

## Usage

First you need to create a YAML configuration file named `vmconfig.yml`, presumably in a dedicated directory for the VM but this is not required.

Here is an example of a configuration file:

```yaml
prototype: w10
name: windows10
cpus: 4
ram: 8G
disk: system.qcow2
os_install:
    - Win10_21H2_English_x64.iso
    - virtio-win-0.1.240.iso
```

Then invoke `vmvm` as follows:

```
vmvm ACTION [CURRENT_DIR]
```

CURRENT_DIR is path to `vmconfig.yml` location. If not specified, current working directory is used.
Note that all non-absolute paths in the config are relative to `vmconfig.yml` location.

| Action    | Description |
| --------- | ----------- |
| `init`    | Create an image file for the first HDD in the config (if does not exist). In the example above `system.qcow2` will be created |
| `install` | Run VM, boot from CD |
| `run`     | Run VM, boot from first HDD |

`install` and `run` both run the VM however the difference is how the boot device is selected.

`install`:
- first boot from CD, after reboot - from first HDD
- exists merely for convenience. Typically you use it only once, to install the OS

`run`:
- always boot from first HDD
- if `need_cd` = `False` (default) then `os_install` is ignored and thus no CD images are mounted
- if `need_cd` = `True` then `os_install` images are mounted

## Configuration Options

### `name`
(Required) Name of your virtual machine

### `prototype`
(Optional) Select a virtual hardware set tuned for particular guest OS.

Values: `default`, `linux`, `w10`, `w11`, `wxp`, `w2k`, `w98`.

If not specified, `default` for current arch is used.

### `cpus`
(Optional) Number of CPUs for your virtual machine

### `ram`
(Optional) Amount of RAM for your virtual machine. You can specify this in gigabytes (G) or megabytes (M).

### `arch`
(Optional) architecture: same as suffix part of `qemu-system-...`.

Values: `i386`, `x86_64`, `aarch64`

### `efi`
(Optional) enable EFI.  True=EFI, False=BIOS

### `secureboot`
(Optional) enable EFI SecureBoot (`OVMF_CODE.secboot.fd`). Has no effect unless `efi` is set to True

### `tpm`
(Optional) software emulation of Trusted Platform Module 2.0. Requires [swtpm](https://www.qemu.org/docs/master/specs/tpm.html#the-qemu-tpm-emulator-device) to be installed

### `bootmenu`
(Optional) enable boot menu

### `floppy`
(Optional) floppy image file

### `disk` (alias `disks`)
(Required) Disk image file. Can also be /dev/... file to pass through a host block device. (Optional) `disks` is an alias for `disk`. Both can be a single path spec or list of path specs.

### `disk_virtio`
(Optional) for disk emulation, specify `blk` to use `virtio-blk`, `scsi` to use `virtio-scsi` or `none` to disable virtio and emulate IDE controller instead.
Applicable only to image file based disks. `blk` theoretically yields best performance. `scsi` is best for large disk arrays. `none` for legacy OSes.

**Performance tip:** `disk_virtio` = `blk` will create one controller for each disk on PCIe bus, so do not use `blk` if more than a few disks. Use `scsi` in such case.

### `os_install`
(Optional) mount these images if action is `install`. Can be a single path spec or list of path specs

### `need_cd`
(Optional) always have ISO images mounted, even if action is not `install`.

### `usb`
(Optional) USB Passthrough. Can be a single device spec or list of specs. Device spec is `vendor:product`.

Example: `usb: 1234:5678`

QEMU user must be able to rw the device. One way to achieve this is to create a file `/etc/udev/rules.d/50-usbpassthrough.rules`

```udev
SUBSYSTEM=="usb", ATTR{idVendor}=="xxxx", ATTR{idProduct}=="xxxx", MODE="0666"
```

### `share_dir_as_fsd`
(Optional) Share a host directory with [virtiofsd](https://virtio-fs.gitlab.io/index.html). Use with Linux guests. This method provides best performance
as well as other useful virtualisation features.

You can mount the directory on the guest as follows:
```
mount -t 9p -o trans=virtio,version=9p2000.L hostshare /mnt/share
```

Example: `share_dir_as_fsd: /home/user/shared`.  Path can be relative to current directory.

### `share_dir_as_fat`
(Optional) Emulate a FAT disk with contents from a directory tree. See [documentation](https://www.qemu.org/docs/master/system/images.html#virtual-fat-disk-images).
Do not use non-ASCII filenames or attempt to write to the FAT directory on the host system while accessing it with the guest system.

### `share_dir_as_floppy`
(Optional) Emulate a floppy with contents from a directory tree. See [documentation](https://www.qemu.org/docs/master/system/images.html#virtual-fat-disk-images).
Do not use non-ASCII filenames or attempt to write to the FAT directory on the host system while accessing it with the guest system.

### `nic`
(Optional) allows to override or disable default network interface card selected by machine type.
`none` disables network card. `virtio` selects `virtio-net-pci` card.
You can also specify exact model name (see `qemu-system-<ARCH> -device help` for list of network devices)

### `nic_forward_ports`
(Optional) Forward local port X to guest port Y.

Example:
```yaml
nic_forward_ports:
    - host: 2222
    guest: 22
```
then on the host you can do:
```
ssh localhost -p 2222
```

### `gpu`
(Optional) GPU model (see `qemu-system-<ARCH> -device help` and "Display devices" section).

### `display`
(Optional) display type (see `qemu-system-<ARCH> -display help`).

Has values such as `gtk`, `sdl` and `none`.

### `sound`
(Optional) Soundcard type.

Values: `hda`, `ac97`, `sb16`, `none`.

### `spice`
(Optional) SPICE server config.
- `unix`: use Unix socket. The path to the socket then will be `/run/user/<UID>/qemu/<machine name>/spice.sock`.
- `auto`: use TCP connection, find the next available port number starting from 5900.
- `(port)`: use TCP connection, specify the port number explicitly.

### `control_socket`
(Optional) enable QMP control socket `/run/user/<UID>/qemu/<machine name>/qmp.sock`. Allows to control the VM with
[`qmp-shell`](https://qemu.readthedocs.io/projects/python-qemu-qmp/en/latest/man/qmp_shell.html) or `qmp-tui` commands
from [`python-qemu-qmp`](https://pypi.org/project/qemu.qmp/) package.

## Ejecting / changing CD images

You can eject or change image for by using QEMU monitor:

```
(qemu) change <device> <path to image>
```

If you run as `install` action and have `os_install` option set then you can use QEMU monitor command above to change the ISO image.
The CD-ROM devices have names like `cddev0`, `cddev1`, etc. Sometimes QEMU monitor does not see these `cddevX` devices due to the bug,
if so happens use `qmp-shell`.

If you don't run as `install` then (since `os_install` is ignored) you are left with any default CD-ROM device present in the machine.
Machine `PC` doesn't allow (or so it seems) to add a ide-cd device without the respective img file node backend, so you are out of luck.
Machine `Q35` has a default device `ide2-cd0` that is always present even if no image specified on the command line.
To view available block devices type in QEMU monitor:

```
(qemu) info block
```


## Handy SMB server

As an alternative to `share_...` config options,  a docker compose is provided in subdirectory `smb` to spin up a SMB server,
to be accessed from guest. Refer to the respective [README](smb/README.md).

## Contributing

If you would like to contribute to this project, please feel free to submit a pull request or open an issue on GitHub.

### Setting Up the Development Environment

1. Install the project dependencies using Poetry: `poetry install --no-root`.
2. If some changes are done in `pyproject.toml`, then `poetry lock` should be used to generate an updated `poetry.lock` file.
3. After making changes in the code, execute `poetry install` to install the package in a virtual environment.
4. Perform tests to validate implemented features.

### Testing

1. Build the Python package: `poetry build`.
2. Build and install the Arch Linux package (if applicable): `makepkg -sri`.

## License

This project is open source and available under the [GPLv3 License](LICENSE).