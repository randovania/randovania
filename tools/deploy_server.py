import asyncio
import copy
import os
import subprocess
from pathlib import Path

_FOLDER = Path(__file__).parent


async def main():
    if os.environ["GITHUB_REF"].startswith("refs/tags/"):
        server_environment = "production"
    else:
        server_environment = "staging"

    remote_host = "randovania.metroidprime.run"
    new_env = copy.copy(os.environ)
    new_env["DOCKER_HOST"] = f"ssh://root@{remote_host}"
    new_env["DOMAIN"] = remote_host
    if server_environment == "production":
        new_env["PATH_PREFIX"] = "randovania"
        new_env["DATA_PATH"] = "/var/randovania/production/data"
        new_env["VERSION"] = os.environ["GITHUB_REF"].split("/")[-1]

    elif server_environment == "staging":
        new_env["PATH_PREFIX"] = "randovania-staging"
        new_env["DATA_PATH"] = "/var/randovania/staging/data"
        new_env["VERSION"] = "sha-{}".format(os.environ["GITHUB_SHA"][:8])
    else:
        raise ValueError(f"Unknown server_environment: {server_environment}")

    subprocess.run(
        [
            "docker-compose",
            "-p", f"randovania-{server_environment}",
            "up",
            "-d",
        ],
        check=True,
        env=new_env,
        cwd=_FOLDER.joinpath("server-docker")
    )


if __name__ == '__main__':
    asyncio.run(main())
