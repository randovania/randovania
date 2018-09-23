import os
import subprocess
import sys
import zipfile

import markdown as markdown

from randovania import VERSION

zip_folder = "randovania-{}".format(VERSION)

subprocess.run([sys.executable, "-m", "PyInstaller", "randovania.spec"])
with zipfile.ZipFile("dist/{}.zip".format(zip_folder), "w") as release_zip:
    release_zip.write("dist/randovania.exe", "{}/randovania.exe".format(zip_folder))
    with open("README.md") as readme_file:
        readme_html = markdown.markdown(readme_file.read())
        release_zip.writestr(zip_folder + "/README.html", readme_html)

    for subdir, _, files in os.walk("randovania-readme"):
        for file in files:
            path = os.path.join(subdir, file)
            release_zip.write(path, "{}/{}".format(zip_folder, path))
