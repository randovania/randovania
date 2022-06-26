import dataclasses
import ftplib
from contextlib import contextmanager
from ftplib import FTP
from pathlib import Path
from typing import Callable

from randovania.lib import status_update_lib


@contextmanager
def ftp_cd(ftp: FTP, pathname: str | None = None):
    """ftp server change folder with statement"""
    original_path = ftp.pwd()
    try:
        if pathname is not None:
            ftp.cwd(pathname)
        yield
    finally:
        ftp.cwd(original_path)


def ftp_is_dir(ftp: FTP, path_name: str) -> bool:
    """check is directory or not"""
    try:
        with ftp_cd(ftp, path_name):
            return True
    except ftplib.error_perm:
        return False


def delete_path(ftp: FTP, path: str, progress_update: Callable[[str], None]):
    try:
        file_list = list(ftp.mlsd(path))
    except ftplib.error_perm as e:
        if str(e) == '501 Not a directory':
            ftp.delete(path)
            return
        elif str(e) in ("550 No such file or directory", "501 No such directory."):
            return
        else:
            raise

    for nested in file_list:
        this_file = f"{path}/{nested[0]}"
        if nested[1]["type"] == "dir":
            delete_path(ftp, this_file, progress_update)
        elif nested[1]["type"] == "file":
            ftp.delete(this_file)
            progress_update(this_file)

    ftp.rmd(path)
    progress_update(path)


@dataclasses.dataclass(frozen=True)
class FtpUploader:
    auth: tuple[str, str] | None
    ip: str
    port: int
    local_path: Path
    remote_path: str

    def __post_init__(self):
        if not self.remote_path.startswith("/"):
            raise ValueError("remote_path must start with /")

    def __call__(self, progress_update: status_update_lib.ProgressUpdateCallable):
        all_files = list(self.local_path.rglob("*"))

        with FTP() as ftp:
            ftp.connect(self.ip, self.port)
            if self.auth is not None:
                ftp.login(*self.auth)
            else:
                ftp.login()

            # Delete any existing remote path
            delete_path(ftp, self.remote_path, lambda name: progress_update(f"Deleting existing file: {name}", -1))

            # Create remote path
            ensure_path = ""
            for part in self.remote_path[1:].split("/"):
                ensure_path += f"/{part}"
                if not ftp_is_dir(ftp, ensure_path):
                    try:
                        ftp.mkd(ensure_path)
                    except ftplib.Error as e:
                        raise RuntimeError(f"Unable to create {ensure_path}") from e

            # Upload files
            for i, file in enumerate(all_files):
                path = self.remote_path + "/" + file.relative_to(self.local_path).as_posix()
                try:
                    if file.is_dir():
                        ftp.mkd(path)

                    elif file.is_file():
                        with file.open("rb") as b:
                            ftp.storbinary(f"STOR {path}", b)

                except ftplib.Error as e:
                    raise RuntimeError(f"Unable to create {path}") from e

                progress_update(f"Uploaded {path}", (i + 1) / len(all_files))
