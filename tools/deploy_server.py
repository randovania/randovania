# /// script
# dependencies = [
# ]
# ///
from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
from pathlib import Path

_FOLDER = Path(__file__).parent


async def deploy(remote_host: str, host2: str, remote_user: str, server_environment: str, version: str):
    new_env = os.environ.copy()
    new_env["DOCKER_HOST"] = f"ssh://{remote_user}@{remote_host}"
    new_env["DOMAIN"] = remote_host
    new_env["VERSION"] = version
    new_env["SERVER_ENVIRONMENT"] = server_environment
    if server_environment == "production":
        new_env["PATH_PREFIX"] = "randovania"
        new_env["DATA_PATH"] = "/var/randovania/production/data"
        new_env["DOMAIN2"] = f"server.{host2}"

    elif server_environment == "staging":
        new_env["PATH_PREFIX"] = "randovania-staging"
        new_env["DATA_PATH"] = "/var/randovania/staging/data"
        new_env["DOMAIN2"] = f"staging.{host2}"
    else:
        raise ValueError(f"Unknown server_environment: {server_environment}")

    stack_file = _FOLDER.joinpath("server-docker", "docker-compose.yml")
    subprocess.run(
        [
            "docker",
            "stack",
            "deploy",
            "-c",
            stack_file,
            f"randovania-{server_environment}",
        ],
        check=True,
        env=new_env,
    )


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default="root")
    parser.add_argument("--host", default="randovania.metroidprime.run")
    parser.add_argument("--host2", default="randovania.org")
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

        version = f"sha-{sha[:8]}"

    await deploy(
        remote_host=args.host,
        host2=args.host2,
        remote_user=args.user,
        server_environment=server_environment,
        version=version,
    )


if __name__ == "__main__":
    asyncio.run(main())
