import os
import time
from pathlib import Path


def wait_for_profiler() -> None:
    if os.environ.get("WAIT_FOR_PROFILER"):
        pid = os.getpid()
        signal_file = Path(".profiler_ready")

        print(f"\n{'=' * 60}")
        print("Waiting for profiler to attach...")
        print(f"Process ID: {pid}")
        print(f"{'=' * 60}\n")
        # Wait for signal file to be created by profiler script
        while not signal_file.exists():
            time.sleep(0.1)
        signal_file.unlink()
