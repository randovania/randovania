"""
Part of the process needed for making universal macOS executables with PyInstaller.

As a requirement to create these executables, all native extensions need to be universal binaries. For that, all
binary wheels installed to the virtual environment used to run PyInstaller must be `universal2`.
This script is responsible for providing these wheels, with managing the venv being left to the GitHub workflow.

Summary:
- For every package installed in the active venv, as said by `uv pip list`.
- Skip packages that don't provide wheels (assuming they're legacy pure-python packages).
- Skip packages that provide only one wheel (assuming they're pure-python packages).
- Skip packages that only provide universal2 wheels (nothing to do!)
- If it provides universal2 and (arm64 or x86_64) wheels, download the universal2 wheel.
- If there's no universal2, but both arm64 and x86_64 wheel, download both and use `delocate` to create an universal2.
- If there's only an arm64 or x86_64 wheel, check if there's a pure python wheel and use that instead.
- All else, fail. Better request to the package maintainers that they provide both wheels.
"""

import asyncio
import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

import aiohttp

from randovania.lib import http_lib


def parse_wheel_filename(url: str) -> dict[str, str]:
    """Parse wheel filename from URL to extract components."""
    filename = url.split("/")[-1]
    if not filename.endswith(".whl"):
        raise ValueError(f"Invalid wheel filename: {filename}")

    # Remove .whl extension
    basename = filename[:-4]

    # Split by '-' but be careful about project names with dashes
    parts = basename.split("-")
    if len(parts) < 5:
        raise ValueError(f"Invalid wheel filename: {filename}")

    # The last 3 parts are always python_tag-abi_tag-platform_tag
    python_tag = parts[-3]
    abi_tag = parts[-2]
    platform_tag = parts[-1]

    return {"python_tag": python_tag, "abi_tag": abi_tag, "platform_tag": platform_tag, "filename": filename}


def is_macos_wheel(platform_tag: str) -> bool:
    """Check if platform tag indicates a macOS wheel."""
    return platform_tag.startswith("macosx_")


def compatible_with_this_interpreter(wheel_info: dict[str, str]) -> bool:
    """Check if wheel matches our criteria (macOS + (abi3 or current Python version))."""

    platform_tag = wheel_info.get("platform_tag", "")
    python_tag = wheel_info.get("python_tag", "")
    abi_tag = wheel_info.get("abi_tag", "")

    # Must be macOS wheel
    if not is_macos_wheel(platform_tag):
        return False

    # Get current Python version tag (e.g., cp313)
    current_python_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"

    # Must be either abi3 or current Python version (e.g., cp313-cp313)
    is_abi3 = abi_tag == "abi3"
    is_current_python = python_tag == current_python_tag and abi_tag == current_python_tag

    return is_abi3 or is_current_python


def parse_macos_platform(platform_tag: str) -> tuple[str, tuple[int, int]]:
    """Parse macOS platform tag to extract architecture and version."""
    if not is_macos_wheel(platform_tag):
        raise ValueError("Not a macOS platform tag")

    # Format: macosx_10_13_x86_64 or macosx_11_0_arm64
    parts = platform_tag.split("_")
    if len(parts) < 4:
        raise ValueError("Invalid macOS platform tag format")

    try:
        major_version = int(parts[1])
        minor_version = int(parts[2])
        # Architecture might be multi-part (e.g., x86_64)
        arch = "_".join(parts[3:])  # x86_64, arm64, universal2, etc.
        return arch, (major_version, minor_version)

    except (ValueError, IndexError):
        raise ValueError("Invalid macOS platform tag format")


def select_best_wheels(matching_wheels: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    """Select one arm64 and one x86_64 wheel, preferring oldest supported OS."""
    arm64_wheels = []
    x86_64_wheels = []

    for wheel_data in matching_wheels:
        platform_tag = wheel_data["wheel_info"]["platform_tag"]
        arch, version = parse_macos_platform(platform_tag)

        if arch == "arm64":
            arm64_wheels.append((wheel_data, version))
        elif arch == "x86_64":
            x86_64_wheels.append((wheel_data, version))

    # Select the wheel with the oldest (lowest) version for each architecture
    selected_wheels = []

    if arm64_wheels:
        # Sort by version (oldest first) and take the first one
        arm64_wheels.sort(key=lambda x: x[1])
        selected_wheels.append(arm64_wheels[0][0])

    if x86_64_wheels:
        # Sort by version (oldest first) and take the first one
        x86_64_wheels.sort(key=lambda x: x[1])
        selected_wheels.append(x86_64_wheels[0][0])

    # Only return if we have both architectures
    if len(selected_wheels) == 2:
        return selected_wheels

    return None


def get_installed_packages() -> set[str]:
    """Get list of installed packages from uv pip list."""
    result = subprocess.run(["uv", "pip", "list", "--format=json"], capture_output=True, text=True, check=True)
    packages_data = json.loads(result.stdout)
    # Extract package names (normalize to lowercase for comparison)
    return {pkg["name"].lower() for pkg in packages_data}


async def download_wheel(session: aiohttp.ClientSession, url: str, dest_dir: Path) -> Path:
    """Download a wheel file to the specified directory using aiohttp."""
    filename = url.split("/")[-1]
    dest_path = dest_dir / filename

    async with session.get(url) as response:
        response.raise_for_status()
        with dest_path.open("wb") as f:
            async for chunk in response.content.iter_chunked(8192):
                f.write(chunk)
    return dest_path


async def download_wheel_to(
    session: aiohttp.ClientSession,
    package_name: str,
    wheel: dict[str, Any],
    wheels_dir: Path,
) -> bool:
    """Download a wheel, checking if it was already downloaded before.

    Returns True if successful (including if already exists), False if failed.
    """

    # Get the filename from the URL
    filename = wheel["url"].split("/")[-1]
    target_path = wheels_dir / filename

    # Skip if file already exists
    if target_path.exists():
        print(f"  ✓ Already exists: {filename}")
        return True

    try:
        wheel_path = await download_wheel(session, wheel["url"], wheels_dir)
        print(f"  ✓ Downloaded: {wheel_path.name}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to download: {e}")
        return False


def calculate_merged_wheel_name(matching_wheels: list[dict[str, Any]]) -> str:
    """Calculate the expected filename for the merged universal2 wheel."""
    # Use the first wheel as a template and modify its platform tag
    first_wheel_info = matching_wheels[0]["wheel_info"]
    filename_parts = first_wheel_info["filename"].split("-")

    # Find the oldest macOS version among the wheels for the universal2 wheel
    min_version = None
    for wheel_data in matching_wheels:
        wheel_info = wheel_data["wheel_info"]
        arch, version = parse_macos_platform(wheel_info["platform_tag"])
        if min_version is None or version < min_version:
            min_version = version

    assert min_version is not None
    # Replace the platform tag with universal2 using the oldest version
    major, minor = min_version
    filename_parts[-1] = f"macosx_{major}_{minor}_universal2.whl"

    return "-".join(filename_parts)


async def merge_wheels(
    session: aiohttp.ClientSession,
    package_name: str,
    matching_wheels: list[dict[str, Any]],
    universal_wheels_dir: Path,
) -> bool:
    """Download wheels and merge them using delocate-merge.

    Returns True if successful (including if already exists), False if failed.
    """

    # Calculate expected merged wheel filename
    expected_filename = calculate_merged_wheel_name(matching_wheels)
    expected_path = universal_wheels_dir / expected_filename

    # Skip if merged wheel already exists
    if expected_path.exists():
        print(f"  ✓ Already exists: {expected_filename}")
        return True

    # Create temporary directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            # Download both wheels concurrently
            download_tasks = [download_wheel(session, wheel_data["url"], temp_path) for wheel_data in matching_wheels]
            wheel_paths = await asyncio.gather(*download_tasks)
        except Exception as e:
            print(f"  ✗ Failed to download wheels for merging: {e}")
            return False

        # Execute delocate-merge to output directory
        try:
            subprocess.run(
                ["delocate-merge", "-w", str(universal_wheels_dir), str(wheel_paths[0]), str(wheel_paths[1])],
                check=True,
                capture_output=True,
                text=True,
            )

            # Check if the expected file was created
            if expected_path.exists():
                print(f"  ✓ Created: {expected_filename}")
                return True
            else:
                print(f"  ✗ Expected file not created: {expected_filename}")
                return False

        except subprocess.CalledProcessError as e:
            print(f"  ✗ delocate-merge failed: {e}")
            if e.stdout:
                print(f"    stdout: {e.stdout}")
            if e.stderr:
                print(f"    stderr: {e.stderr}")
            return False


def is_pure_python_wheel(wheel_info: dict) -> bool:
    return wheel_info["abi_tag"] == "none" and wheel_info["platform_tag"] == "any" and wheel_info["python_tag"] == "py3"


async def main() -> int:
    """Main function to process uv.lock file.

    Returns 0 for success, 1 for failure.
    """
    lock_file = Path(__file__).parents[1] / "uv.lock"

    universal_wheels_dir = Path.cwd() / "universal_wheels"
    universal_wheels_dir.mkdir(exist_ok=True)

    # Get list of installed packages
    print("Getting list of installed packages...")
    installed_packages = get_installed_packages()
    print(f"Found {len(installed_packages)} installed packages")
    print()

    # Read and parse the lock file
    with lock_file.open("rb") as f:
        data = tomllib.load(f)

    packages = data["package"]

    # Track failures
    failed_packages = []

    # Create aiohttp session for downloads
    async with http_lib.http_session() as session:
        for package in packages:
            package_name = package["name"]
            wheels = package.get("wheels", [])

            # Skip packages not in installed list
            if package_name.lower() not in installed_packages:
                continue

            # Skip packages with no wheels or just pure python wheels
            if len(wheels) <= 1:
                continue

            # Filter for macOS wheels
            pure_wheel = None
            matching_wheels = []
            for wheel in wheels:
                wheel_info = parse_wheel_filename(wheel["url"])
                if compatible_with_this_interpreter(wheel_info):
                    matching_wheels.append({"url": wheel["url"], "wheel_info": wheel_info})
                elif is_pure_python_wheel(wheel_info):
                    pure_wheel = {"url": wheel["url"], "wheel_info": wheel_info}

            # Skip if no matching wheels found
            if not matching_wheels:
                continue

            # Check for universal2 wheel and categorize other wheels
            universal2_wheel = None
            platform_specific_wheels = []

            for wheel_data in matching_wheels:
                wheel_info = wheel_data["wheel_info"]
                arch, version = parse_macos_platform(wheel_info["platform_tag"])

                if arch == "universal2":
                    universal2_wheel = wheel_data
                else:
                    platform_specific_wheels.append(wheel_data)

            # Skip packages that only have universal2 wheels
            if universal2_wheel and not platform_specific_wheels:
                continue

            # Print the package and its matching wheels
            print(f"Package: {package_name}")
            for wheel_data in matching_wheels:
                wheel_info = wheel_data["wheel_info"]
                arch, version = parse_macos_platform(wheel_info["platform_tag"])
                print(f"    - {wheel_info['filename']} ({arch}, macOS {version[0]}.{version[1]})")

            # Prefer universal2 wheel if available, especially when platform-specific wheels also exist
            if universal2_wheel:
                success = await download_wheel_to(session, package_name, universal2_wheel, universal_wheels_dir)
                if not success:
                    failed_packages.append(package_name)

            else:
                # Only try merging if no universal2 wheel is available
                selected_wheels = select_best_wheels(platform_specific_wheels)
                if selected_wheels:
                    success = await merge_wheels(session, package_name, selected_wheels, universal_wheels_dir)
                    if not success:
                        failed_packages.append(package_name)

                elif pure_wheel is not None:
                    # If there's no wheels to merge, but there's a pure wheel try that
                    success = await download_wheel_to(session, package_name, pure_wheel, universal_wheels_dir)
                    if not success:
                        failed_packages.append(package_name)
                else:
                    print("  ✗ Could not find suitable arm64 and x86_64 wheels to merge.")
                    failed_packages.append(package_name)

            print()

    # Report results and return appropriate exit code
    if failed_packages:
        print(f"\nFailed to process {len(failed_packages)} package(s): {', '.join(failed_packages)}")
        return 1
    else:
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
