#
# https://www.qemu.org/docs/master/specs/tpm.html#the-qemu-tpm-emulator-device
#

import os
import subprocess
from shutil import rmtree


class TPMManager:
    def __init__(self, tag: str):
        self._tpmdir = f"/tmp/qemu-tpm-{tag}"
        self._process = None

    def run(self) -> None:
        if not os.path.exists(self._tpmdir):
            os.mkdir(self._tpmdir)

        if self._process is None:
            self._process = subprocess.Popen(
                [
                    "swtpm",
                    "socket",
                    "--tpmstate",
                    f"dir={self._tpmdir}",
                    "--ctrl",
                    f"type=unixio,path={self.sock}",
                    "--tpm2",
                    #'--log', 'level=20',
                ]
            )

    def shutdown(self) -> None:
        if self._process is not None:
            self._process.terminate()
            self._process.wait()
            self._process = None
        if os.path.exists(self._tpmdir):
            rmtree(self._tpmdir)

    @property
    def sock(self) -> str:
        return f"{self._tpmdir}/swtpm-sock"
