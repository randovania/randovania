import json
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import markdown

from randovania import VERSION
from randovania.cli import prime_database

_ROOT_FOLDER = Path(__file__).parents[1]
zip_folder = "randovania-{}".format(VERSION)


def open_zip(platform_name: str) -> zipfile.ZipFile:
    return zipfile.ZipFile(_ROOT_FOLDER.joinpath(f"dist/{zip_folder}-{platform_name}.zip"),
                           "w", compression=zipfile.ZIP_DEFLATED)


def main():
    package_folder = Path("dist", "randovania")
    if package_folder.exists():
        shutil.rmtree(package_folder, ignore_errors=False)

    app_folder = Path("dist", "Randovania.app")
    if app_folder.exists():
        shutil.rmtree(app_folder, ignore_errors=False)

    with _ROOT_FOLDER.joinpath("randovania", "data", "json_data", "prime2.json").open() as json_data_file:
        json_data = json.load(json_data_file)
    prime_database.export_as_binary(json_data,
                                    _ROOT_FOLDER.joinpath("randovania", "data", "binary_data", "prime2.bin"))

    subprocess.run([sys.executable, "-m", "PyInstaller",
                    "randovania.spec"],
                   check=True)

    if platform.system() == "Windows":
        create_windows_zip(package_folder)
    elif platform.system() == "Darwin":
        create_macos_zip(app_folder)


def create_windows_zip(package_folder):
    with open_zip("windows") as release_zip:
        for f in package_folder.glob("**/*"):
            print("Adding", f)
            release_zip.write(f, "{}/{}".format(zip_folder, f.relative_to(package_folder)))

        add_readme_to_zip(release_zip)


def create_macos_zip(folder_to_pack: Path):
    with tarfile.open(_ROOT_FOLDER.joinpath(f"dist/{zip_folder}-macos.tar.gz"), "w:gz") as release_zip:
        release_zip.add(folder_to_pack, f"{zip_folder}/Randovania.app")


def add_readme_to_zip(release_zip):
    with _ROOT_FOLDER.joinpath("README.md").open() as readme_file:
        readme_html = markdown.markdown(readme_file.read())
        release_zip.writestr(zip_folder + "/README.html", readme_html)


if __name__ == '__main__':
    main()
