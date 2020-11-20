import asyncio
import atexit
import copy
import logging
import os
import re
import subprocess
from pathlib import Path

_FOLDER = Path(__file__).parent
AGENT_OUTPUT_PATTERN = re.compile(
    r'SSH_AUTH_SOCK=(?P<socket>[^;]+).*SSH_AGENT_PID=(?P<pid>\d+)', re.MULTILINE | re.DOTALL)


def _kill_agent():
    logging.info('killing previously started ssh-agent')
    subprocess.run(['ssh-agent', '-k'])
    del os.environ['SSH_AUTH_SOCK']
    del os.environ['SSH_AGENT_PID']


def _setup_agent():
    process = subprocess.run(['ssh-agent', '-s'], stdout=subprocess.PIPE, universal_newlines=True)
    match = AGENT_OUTPUT_PATTERN.search(process.stdout)
    if match is None:
        raise Exception('Could not parse ssh-agent output. It was: {}'.format(process.stdout))
    agent_data = match.groupdict()
    logging.info('ssh agent data: {}'.format(agent_data))
    logging.info('exporting ssh agent environment variables')
    os.environ['SSH_AUTH_SOCK'] = agent_data['socket']
    os.environ['SSH_AGENT_PID'] = agent_data['pid']
    atexit.register(_kill_agent)


async def main():
    if os.environ["GITHUB_REF"].startswith("refs/tags/"):
        server_environment = "production"
    else:
        server_environment = "staging"

    remote_host = "randovania.metroidprime.run"
    ssh_key = os.environ["DEPLOYMENT_KEY"]

    _setup_agent()
    subprocess.run(['ssh-add', "-"], check=True, input=ssh_key, text=True)

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
