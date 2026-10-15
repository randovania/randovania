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
from typing import Literal

_FOLDER = Path(__file__).parent


async def deploy(
    base_host: str,
    legacy_host: str,
    remote_user: str,
    server_environment: Literal["production", "staging"],
    version: str,
    context: str | None,
) -> None:
    new_env = os.environ.copy()

    new_env["APP_DOMAIN"] = f"{server_environment}.{base_host}"
    new_env["ADMIN_DOMAIN"] = f"server.{base_host}"
    new_env["LEGACY_DOMAIN"] = legacy_host
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

    # Check `randovania-staging` over production's `randovania`.
    new_env["LEGACY_REDIRECT_PRIORITY"] = str(200 + len(new_env["PATH_PREFIX"]))

    context_args = []
    if context is not None:
        context_args = ["--context", context]
    else:
        new_env["DOCKER_HOST"] = f"ssh://{remote_user}@server.{base_host}"

    stack_file = _FOLDER.joinpath("server-docker", "docker-compose.yml")
    subprocess.run(
        [
            "docker",
            *context_args,
            "stack",
            "deploy",
            "--detach=true",
            "-c",
            stack_file,
            f"randovania-{server_environment}",
        ],
        check=True,
        env=new_env,
    )


async def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--user", default="root")
    group.add_argument("--context")
    parser.add_argument("--host", default="randovania.org")
    parser.add_argument("--legacy-host", default="randovania.metroidprime.run")
    version = parser.add_mutually_exclusive_group()
    version.add_argument("--ref")
    version.add_argument("--sha")
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
        base_host=args.host,
        legacy_host=args.legacy_host,
        remote_user=args.user,
        server_environment=server_environment,
        version=version,
        context=args.context,
    )


if __name__ == "__main__":
    asyncio.run(main())
