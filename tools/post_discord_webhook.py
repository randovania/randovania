import asyncio
import datetime
import os
import pprint
import subprocess

import aiohttp

from randovania import VERSION


async def post_to_discord():
    try:
        current_branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                        check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
    except Exception:
        current_branch = "<Unknown Branch>"

    git_result = subprocess.run(["git", "show"], check=True, stdout=subprocess.PIPE, text=True).stdout.split("\n")
    commit_hash = git_result[0].split()[1]

    message = ""
    for line in git_result[4:]:
        if line.startswith("diff --git"):
            break
        else:
            message += line
            message += "\n"

    run_id = os.environ["GITHUB_RUN_ID"]
    org_name = "randovania"
    repo_name = "randovania"

    # # TODO: querying for artifacts during the same id gets nothing downloaded
    # async with aiohttp.ClientSession() as session:
    #     session.headers['Authorization'] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    #
    #     run_details_url = f"https://api.github.com/repos/{org_name}/{repo_name}/actions/runs/{run_id}"
    #     print(f"> Get run details: {run_details_url}")
    #     async with session.get(run_details_url, raise_for_status=True) as response:
    #         run_details = await response.json()
    #         pprint.pprint(run_details)
    #         check_suite_id = run_details["check_suite_id"]
    #
    #     artifacts_url = f"https://api.github.com/repos/{org_name}/{repo_name}/actions/runs/{run_id}/artifacts"
    #     print(f"> Get artifact details: {artifacts_url}")
    #     async with session.get(artifacts_url, raise_for_status=True) as response:
    #         artifacts = await response.json()
    #         pprint.pprint(artifacts)

    fields = [
        {
            "name": artifact.replace("Executable", "").replace("Randovania", "").strip(),
            "value": f"[Download](https://nightly.link/{org_name}/{repo_name}/"
                     f"actions/runs/{run_id}/{artifact.replace(' ', '%20')}.zip)",
            "inline": True
        }
        for artifact in os.listdir("packages")
    ]

    webhook_data = {
        "embeds": [{
            "color": 0x2ecc71,
            "title": f"{current_branch} - Randovania {VERSION}",
            "url": f"https://github.com/randovania/randovania/commit/{commit_hash}",
            "description": message.strip(),
            "fields": fields,
            "timestamp": datetime.datetime.now().isoformat()
        }]
    }
    pprint.pprint(webhook_data)

    webhook_url = os.environ["DISCORD_WEBHOOK"]
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=webhook_data, raise_for_status=True) as response:
            print(await response.text())


if __name__ == '__main__':
    asyncio.run(post_to_discord())
