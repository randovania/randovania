import dataclasses
import ftplib
import logging
from ftplib import FTP
from pathlib import Path
from typing import Optional, Callable

from randovania.lib import status_update_lib


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
    auth: Optional[tuple[str, str]]
    ip: str
    port: int
    local_path: Path
    remote_path: str

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
            for part in self.remote_path.split("/"):
                ensure_path += f"/{part}"
                try:
                    ftp.mkd(ensure_path)
                except ftplib.error_perm as e:
                    logging.warning("Unable to create %s: %s", ensure_path, str(e))

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
