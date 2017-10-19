import subprocess
import sys
import zipfile

import markdown as markdown

from randovania import VERSION

zip_folder = "randovania-{}".format(VERSION)

randomizer_files = {
    "Randomizer/Randomizer/lzo2.dll": zip_folder + "/lzo2.dll",
    "Randomizer/Randomizer/readme.txt": zip_folder + "/Randomizer-readme.txt",
    "Randomizer/Randomizer/Randomizer.exe": zip_folder + "/Randomizer.exe",
    "Randomizer/Randomizer/zlib1.dll": zip_folder + "/zlib1.dll",
}

subprocess.run([sys.executable, "-m", "PyInstaller", "randovania.spec"])
with zipfile.ZipFile("{}.zip".format(zip_folder), "w") as release_zip:
    release_zip.write("dist/randovania.exe", "{}/randovania.exe".format(zip_folder))
    release_zip.write("scripts/interactive_randovania.bat", "{}/interactive_randovania.bat".format(zip_folder))
    with open("README.md") as readme_file:
        readme_html = markdown.markdown(readme_file.read())
        release_zip.writestr(zip_folder + "/README.html", readme_html)

    with zipfile.ZipFile("tools/Randomizer.zip") as randomizer_zip:
        for info in randomizer_zip.infolist():
            info: zipfile.ZipInfo = info
            if info.filename in randomizer_files:
                release_zip.writestr(
                    randomizer_files[info.filename],
                    randomizer_zip.read(info.filename)
                )
