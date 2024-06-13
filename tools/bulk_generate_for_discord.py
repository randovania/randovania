import argparse
import datetime
import io
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", required=True)
    parser.add_argument("--preset", default="Starter Preset")
    parser.add_argument("--target-seed-count", type=int, default=100)
    parser.add_argument("--process-count", type=int, default=6)
    args = parser.parse_args()

    this_dir = Path(__file__).parent

    target_game = args.game
    target_preset = args.preset
    target_seed_count = args.target_seed_count
    process_count = args.process_count

    output_path = this_dir.joinpath("bulk")
    rdvgame_path = output_path / "rdvgame"
    report_path = output_path / "report.json"
    webhook_url = os.environ["WEBHOOK_URL"]

    # Get permalink
    permalink = subprocess.run(
        [
            sys.executable,
            "-m",
            "randovania",
            "layout",
            "permalink",
            "--name",
            f"{target_game}/{target_preset}",
            "--seed-number",
            "1000",
            "--development",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    # Delete old path
    shutil.rmtree(output_path, ignore_errors=True)
    output_path.mkdir(parents=True)

    # Batch generate
    before = datetime.datetime.now()
    generate_log = subprocess.run(
        [
            sys.executable,
            "-m",
            "randovania",
            "layout",
            "batch-distribute",
            "--process-count",
            str(process_count),
            permalink,
            str(target_seed_count),
            os.fspath(rdvgame_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    duration = datetime.datetime.now() - before
    print(generate_log)

    generated_count = sum(1 for _ in rdvgame_path.rglob("*"))
    failed_count = target_seed_count - generated_count
    timed_out_count = generate_log.count("Timeout reached when validating possibility")

    # Analyze
    subprocess.run(
        [
            sys.executable,
            os.fspath(this_dir.joinpath("log_analyzer.py")),
            rdvgame_path,
            report_path,
        ],
        check=True,
    )

    # Pack everything
    with tarfile.TarFile("games.tar.gz", "w") as games_tar:
        games_tar.add(rdvgame_path, arcname=rdvgame_path.relative_to(output_path))
        games_tar.add(report_path, arcname=report_path.relative_to(output_path))
        games_tar.addfile(
            tarfile.TarInfo("generation.log"),
            io.BytesIO(generate_log.encode("utf-8")),
        )

    real_time = str(duration)

    # Send report
    subprocess.run(
        [
            sys.executable,
            os.fspath(this_dir.joinpath("send_report_to_discord.py")),
            "--title",
            f"Batch report for {target_game}",
            "--field",
            f"Generated:{generated_count} out of {target_seed_count}",
            "--field",
            f"Timed out:{timed_out_count} out of {failed_count} failures",
            "--field",
            f"Preset:{target_preset}",
            "--field",
            f"Elapsed real time:{real_time}",
            "--attach",
            "games.tar.gz",
            "--webhook",
            webhook_url,
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
