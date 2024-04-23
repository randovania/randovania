from __future__ import annotations

import asyncio
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import aiohttp
import markdown
import tenacity

import randovania
from randovania import VERSION
from randovania.cli import database
from randovania.games import default_data
from randovania.games.game import RandovaniaGame
from randovania.interface_common import installation_check
from randovania.lib import json_lib
from randovania.lib.enum_lib import iterate_enum

_ROOT_FOLDER = Path(__file__).parents[1]
_NINTENDONT_DOWNLOAD_URL = "https://github.com/randovania/Nintendont/releases/download/v5-multiworld/boot.dol"
zip_folder = f"randovania-{VERSION}"


def is_production():
    return os.getenv("PRODUCTION", "false") == "true"


def open_zip(platform_name: str) -> zipfile.ZipFile:
    return zipfile.ZipFile(
        _ROOT_FOLDER.joinpath(f"dist/{zip_folder}-{platform_name}.zip"), "w", compression=zipfile.ZIP_DEFLATED
    )


def get_dotnet_url() -> str:
    if platform.system() == "Windows":
        return "https://dot.net/v1/dotnet-install.ps1"

    return "https://dot.net/v1/dotnet-install.sh"


@tenacity.retry(
    stop=tenacity.stop_after_attempt(5),
    retry=tenacity.retry_if_exception_type(aiohttp.ClientConnectorError),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=30),
)
async def download_nintendont():
    headers = None
    if "GITHUB_TOKEN" in os.environ:
        headers = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}

    async with aiohttp.ClientSession(headers=headers) as session:
        print(f"Downloading {_NINTENDONT_DOWNLOAD_URL}")
        async with session.get(_NINTENDONT_DOWNLOAD_URL) as download_response:
            download_response.raise_for_status()
            dol_bytes = await download_response.read()

        final_dol_path = _ROOT_FOLDER.joinpath("randovania", "data", "nintendont", "boot.dol")
        print(f"Saving to {final_dol_path}")
        final_dol_path.write_bytes(dol_bytes)


async def download_dotnet() -> None:
    # Windows is finnicky about the file extension. Not sure why.
    script_path = _ROOT_FOLDER.joinpath("dotnet.ps1" if platform.system() == "Windows" else "dotnet.sh")
    dotnet_path = _ROOT_FOLDER.joinpath("randovania", "data", "dotnet_runtime")
    async with aiohttp.ClientSession() as session:
        url = get_dotnet_url()
        print(f"Downloading {url}")
        async with session.get(url) as response:
            response.raise_for_status()
            script_bytes = await response.read()

            print(f"Saving to {script_path}")
            script_path.write_bytes(script_bytes)

    print("Executing dotnet script")
    # I would like to use Unix-style arguments everywhere, but sadly those aren't fully supported. PS-Style are tho.
    args = [
        f"{script_path}",
        "-Version",
        "latest",
        "-InstallDir",
        f"{dotnet_path}",
        "-Runtime",
        "dotnet",
    ]
    if platform.system() == "Windows":
        args = ["powershell.exe", *args]
    else:
        subprocess.run(["chmod", "+x", script_path], check=True)
        args = ["bash", *args]
    subprocess.run(
        args,
        check=True,
    )
    print("Removing downloaded script")
    script_path.unlink()


def write_obfuscator_secret(path: Path, secret: bytes):
    numbers = str(list(secret))
    path.write_text(
        f"""# Generated file
secret = b"".join(
    bytes([x]) for x in
    {numbers}
)
"""
    )


def write_frozen_file_list(package_folder: Path) -> None:
    internal = package_folder.joinpath("_internal")
    json_lib.write_path(
        internal.joinpath("data", "frozen_file_list.json"), installation_check.hash_everything_in(internal)
    )


async def main():
    package_folder = Path("dist", "randovania")
    if package_folder.exists():
        shutil.rmtree(package_folder, ignore_errors=False)

    app_folder = Path("dist", "Randovania.app")
    if app_folder.exists():
        shutil.rmtree(app_folder, ignore_errors=False)

    for game in iterate_enum(RandovaniaGame):
        database.export_as_binary(
            default_data.read_json_then_binary(game)[1],
            _ROOT_FOLDER.joinpath("randovania", "data", "binary_data", f"{game.value}.bin"),
        )

    icon_path = randovania.get_icon_path()
    shutil.copyfile(icon_path, icon_path.with_name("executable_icon.ico"))

    if (secret := os.environ.get("OBFUSCATOR_SECRET")) is not None:
        write_obfuscator_secret(
            _ROOT_FOLDER.joinpath("randovania", "lib", "obfuscator_secret.py"),
            secret.encode("ascii"),
        )

    if is_production():
        server_suffix = "randovania"
        client_id = 618134325921316864
    else:
        server_suffix = "randovania-staging"
        client_id = 887825192208969828

    configuration = {
        "discord_client_id": client_id,
        "server_address": f"https://randovania.metroidprime.run/{server_suffix}",
        "socketio_path": f"/{server_suffix}/socket.io",
        "sentry_urls": {"client": os.environ.get("SENTRY_CLIENT_URL")},
    }
    json_lib.write_path(_ROOT_FOLDER.joinpath("randovania", "data", "configuration.json"), configuration)

    await download_nintendont()

    await download_dotnet()

    # HACK: pyintaller calls lipo/codesign on macOS and frequently timeout in github actions
    # There's also timeouts on Windows so we're expanding this to everyone
    print("Will patch timeout in PyInstaller compat")
    import PyInstaller.compat

    compat_path = Path(PyInstaller.compat.__file__)
    compat_text = compat_path.read_text().replace("timeout=60", "timeout=180")
    compat_path.write_text(compat_text)

    subprocess.run([sys.executable, "-m", "PyInstaller", "randovania.spec"], check=True)

    if platform.system() == "Windows":
        create_windows_zip(package_folder)
        write_frozen_file_list(package_folder)
    elif platform.system() == "Darwin":
        create_macos_zip(app_folder)
    elif platform.system() == "Linux":
        create_linux_zip(package_folder)
        write_frozen_file_list(package_folder)
    else:
        raise ValueError(f"Unknown system: {platform.system()}")


def create_windows_zip(package_folder):
    if is_production():
        with open_zip("windows") as release_zip:
            for f in package_folder.glob("**/*"):
                print("Adding", f)
                release_zip.write(f, f"{zip_folder}/{f.relative_to(package_folder)}")

            add_readme_to_zip(release_zip)
    else:
        zip_file = os.fspath(_ROOT_FOLDER.joinpath(f"dist/{zip_folder}-windows.7z"))
        subprocess.run(["7z", "a", "-mx=7", "-myx=7", zip_file, os.fspath(package_folder)], check=True)
        subprocess.run(["7z", "rn", zip_file, os.fspath(package_folder), zip_folder], check=True)


def create_macos_zip(folder_to_pack: Path):
    output = f"dist/{zip_folder}-macos.tar.gz"
    with tarfile.open(_ROOT_FOLDER.joinpath(f"dist/{zip_folder}-macos.tar.gz"), "w:gz") as release_zip:
        print(f"Creating {output} from {folder_to_pack}.")
        release_zip.add(folder_to_pack, f"{zip_folder}/Randovania.app")
        print("Finished.")


def create_linux_zip(folder_to_pack: Path):
    output = _ROOT_FOLDER.joinpath(f"dist/{zip_folder}-linux.tar.gz")
    with tarfile.open(output, "w:gz") as release_zip:
        print(f"Creating {output} from {folder_to_pack}.")
        release_zip.add(folder_to_pack, zip_folder)
        print("Finished.")


def add_readme_to_zip(release_zip):
    with _ROOT_FOLDER.joinpath("README.md").open() as readme_file:
        readme_html = markdown.markdown(readme_file.read())
        release_zip.writestr(zip_folder + "/README.html", readme_html)


if __name__ == "__main__":
    asyncio.run(main())
