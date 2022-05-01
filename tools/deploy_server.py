import argparse
import asyncio
import copy
import os
import subprocess
from pathlib import Path

_FOLDER = Path(__file__).parent


async def deploy(remote_host: str, remote_user: str, server_environment: str, version: str):
    new_env = copy.copy(os.environ)
    new_env["DOCKER_HOST"] = f"ssh://{remote_user}@{remote_host}"
    new_env["DOMAIN"] = remote_host
    new_env["VERSION"] = version
    new_env["SERVER_ENVIRONMENT"] = server_environment
    if server_environment == "production":
        new_env["PATH_PREFIX"] = "randovania"
        new_env["DATA_PATH"] = "/var/randovania/production/data"

    elif server_environment == "staging":
        new_env["PATH_PREFIX"] = "randovania-staging"
        new_env["DATA_PATH"] = "/var/randovania/staging/data"
    else:
        raise ValueError(f"Unknown server_environment: {server_environment}")

    stack_file = _FOLDER.joinpath("server-docker", "docker-compose.yml")
    subprocess.run(
        [
            "docker",
            "stack",
            "deploy",
            "-c", stack_file,
            f"randovania-{server_environment}",
        ],
        check=True,
        env=new_env,
    )


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default="root")
    parser.add_argument("--host", default="randovania.metroidprime.run")
    parser.add_argument("--ref")
    parser.add_argument("--sha")
    args = parser.parse_args()

    ref = args.ref
    if ref is None:
        ref = os.environ["GITHUB_REF"]

    if ref.startswith("refs/tags/"):
        server_environment = "production"
        version = ref.split("/")[-1]
    else:
        server_environment = "staging"
        sha = args.sha
        if sha is None:
            sha = os.environ["GITHUB_SHA"]

        version = "sha-{}".format(sha[:8])

    await deploy(
        remote_host=args.host,
        remote_user=args.user,
        server_environment=server_environment,
        version=version,
    )


if __name__ == '__main__':
    asyncio.run(main())
