import asyncio
import os
from pathlib import Path

import aiohttp

from randovania import VERSION

_ROOT_FOLDER = Path(__file__).parents[1]
API_URL = 'https://api.bintray.com'
REPOSITORY_USER = 'randovania'
REPOSITORY = 'randovania'
PACKAGE = 'randovania'


async def main():
    release_files = [f for f in _ROOT_FOLDER.joinpath("dist").glob("randovania-*.*")]
    print(f"Found {len(release_files)} files at {_ROOT_FOLDER.joinpath('dist')}:")
    for f in release_files:
        print(f"* {f}")

    print("\nLooking for a valid file...")
    zip_file = None
    for f in release_files:
        if f.name.endswith(".zip") or f.name.endswith(".tar.gz") or f.name.endswith(".7z"):
            zip_file = f
            print(f"Upload release at {zip_file}")
            break
        else:
            print(f"* {f.name} is not a .zip or .tar.gz or .7z")

    if zip_file is None:
        raise RuntimeError(f"No valid release file found.")

    bintray_user = os.environ["BINTRAY_USER"]
    bintray_password = os.environ["BINTRAY_API_KEY"]

    upload_url = f"{API_URL}/content/{REPOSITORY_USER}/{REPOSITORY}/{PACKAGE}/{VERSION}/{zip_file.name};publish=1"
    async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(bintray_user, bintray_password)) as session:
        async with session.put(upload_url, data=zip_file.open("rb")) as response:
            print(await response.text())


if __name__ == '__main__':
    asyncio.run(main())
