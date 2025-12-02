#!/usr/bin/env python3
"""
Unified tool for working with py-spy profiler.

Commands:
    collect     - Profile a Python process with py-spy
    filter      - Filter py-spy raw output to remove noise
    check-function - Analyze where time is spent in a specific function
    chart       - Generate function statistics chart from raw profile

Examples:
    python pyspy_tools.py collect -o profile.raw -f raw -- -m randovania layout generate-from-presets ...
    python pyspy_tools.py filter profile.raw > profile.filtered
    python pyspy_tools.py check-function profile.raw my_function_name
    python pyspy_tools.py chart profile.raw
"""

import argparse
import csv
import os
import re
import subprocess
import sys
import time
import typing
from collections import Counter, defaultdict
from pathlib import Path


def parse_raw_profile(file: typing.TextIO) -> list[list[str]]:
    """Parse a py-spy raw format file into a list of stack traces."""
    traces = []
    for line in file:
        line = line.strip()
        if not line:
            continue
        # Each line is: frame1;frame2;frame3;... count
        parts = line.rsplit(" ", 1)
        if len(parts) != 2:
            continue
        stack_str, count_str = parts
        try:
            count = int(count_str)
        except ValueError:
            continue

        stack_str = stack_str.replace("\\", "/")

        # Split the stack trace by semicolon
        frames = stack_str.split(";")
        # Add this trace 'count' times (usually just 1)
        for _ in range(count):
            traces.append(frames)

    return traces


# ============================================================================
# COLLECT COMMAND - Profile with py-spy
# ============================================================================


def cmd_collect(args):
    """Profile Randovania with py-spy."""
    # Set environment variables
    env = os.environ.copy()
    env["WAIT_FOR_PROFILER"] = "1"
    env["PYTHONUNBUFFERED"] = "1"  # Disable Python output buffering

    print("Starting Randovania process...", flush=True)

    # Start the Python process
    process = subprocess.Popen(
        [sys.executable] + args.python_command,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    print(f"Process started with PID: {process.pid}")

    # Wait for the process to print the ready message
    print("Waiting for process to reach profiling point...")
    target_pid = None

    for line in process.stdout:
        print(line, end="", flush=True)
        if "Process ID:" in line:
            # Extract PID from the line
            try:
                target_pid = int(line.split("Process ID:")[-1].strip())
                break
            except (ValueError, IndexError):
                pass

    if target_pid is None:
        print("Failed to detect process ready state")
        process.terminate()
        sys.exit(1)

    print("\nStarting py-spy profiler...")

    # Build py-spy command
    pyspy_cmd = [
        "py-spy",
        "record",
        "--native",
        "--pid",
        str(target_pid),
        "--rate",
        str(args.rate),
        "--format",
        args.format,
        "-o",
        args.output,
    ]

    # Start py-spy
    pyspy_process = subprocess.Popen(pyspy_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    print(f"py-spy attached to process {target_pid}")
    print(f"Profiling to: {args.output}")

    # Signal the main process to continue
    signal_file = Path(".profiler_ready")
    signal_file.touch()

    print()
    print("Process continuing execution...")
    print()

    # Continue streaming output from the main process
    try:
        if process.stdout:
            for line in process.stdout:
                print(line, end="", flush=True)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        process.terminate()
        pyspy_process.terminate()

    # Wait for process to complete
    exit_code = process.wait()

    print()
    print(f"Process completed with exit code: {exit_code}")

    # Wait for py-spy to finish writing
    time.sleep(1)
    pyspy_process.terminate()
    pyspy_process.wait()

    # Print py-spy output
    if pyspy_process.stdout:
        pyspy_output = pyspy_process.stdout.read()
        if pyspy_output:
            print("\npy-spy output:")
            print(pyspy_output)

    if Path(args.output).exists():
        print(f"Profile saved to: {args.output}")
    else:
        print("Warning: Profile file not found")

    sys.exit(exit_code)


# ============================================================================
# FILTER COMMAND - Filter py-spy raw output
# ============================================================================


def remove_std_allocator(frame: str) -> str:
    """
    Remove std::allocator<...> from C++ template names.
    Handles nested templates by counting angle brackets.
    """
    result = []
    i = 0
    while i < len(frame):
        # Look for "std::allocator<"
        if frame[i:].startswith("std::allocator<"):
            # Find the matching closing >
            depth = 1
            j = i + len("std::allocator<")
            while j < len(frame) and depth > 0:
                if frame[j] == "<":
                    depth += 1
                elif frame[j] == ">":
                    depth -= 1
                j += 1

            # Skip the allocator and any following comma+space
            i = j
            if i < len(frame) and frame[i : i + 2] == ", ":
                i += 2
            elif i < len(frame) and frame[i] == ",":
                i += 1
        else:
            result.append(frame[i])
            i += 1

    return "".join(result)


def cmd_filter(args):
    """Filter py-spy raw format to remove noise."""
    file = args.raw_file.open() if args.raw_file.name != "-" else sys.stdin
    traces = parse_raw_profile(file)

    count = 1

    for i, frames in enumerate(traces):
        if i + 1 < len(traces) and traces[i + 1] == frames:
            # Skip duplicate consecutive traces
            count += 1
            continue

        filtered_frames = []

        for frame in frames:
            if args.exclude_frozen and "<frozen " in frame:
                continue
            if args.exclude_asyncio and ("(asyncio/" in frame or "_asyncio.pyd" in frame):
                continue
            if args.exclude_python_api and "(python312.dll)" in frame:
                continue
            if args.exclude_python_exe and "(python.exe)" in frame:
                continue

            # Remove std::allocator from C++ template names
            frame = remove_std_allocator(frame)

            filtered_frames.append(frame)

        print(f"{';'.join(filtered_frames)} {count}")
        count = 1


# ============================================================================
# CHECK-FUNCTION COMMAND - Analyze function hotspots
# ============================================================================


def extract_function_samples(traces: list[list[str]], function_name: str) -> list[list[str]]:
    """Extract all traces that contain the given function."""
    matching_traces = []
    for trace in traces:
        for frame in trace:
            if function_name in frame:
                matching_traces.append(trace)
                break
    return matching_traces


def analyze_function_hotspots(traces: list[list[str]], function_name: str) -> dict[str, int]:
    """
    For each trace containing the function, find the deepest (most specific) frame
    within that function and count occurrences.
    """
    line_counts = Counter()

    for trace in traces:
        # Find all frames in this function
        function_frames = []
        for i, frame in enumerate(trace):
            if function_name in frame:
                function_frames.append((i, frame))

        if not function_frames:
            continue

        # Get the deepest (last) frame in the function - most specific location
        _, deepest_frame = function_frames[-1]
        line_counts[deepest_frame] += 1

    return line_counts


def format_frame(frame: str) -> tuple[str, str, str]:
    """Parse a frame string to extract function name, file, and line number."""
    # Format is typically: function_name (file.py:line)
    if "(" in frame and ")" in frame:
        func_part = frame[: frame.rfind("(")].strip()
        location_part = frame[frame.rfind("(") + 1 : frame.rfind(")")].strip()

        if ":" in location_part:
            file_part, line_part = location_part.rsplit(":", 1)
            return func_part, file_part, line_part
        else:
            return func_part, location_part, ""
    else:
        return frame, "", ""


def map_cpp_to_python_line(cpp_file: Path, cpp_line: int, context_lines: int = 50) -> tuple[str, int] | None:
    """
    Map a C++ line number back to the original Python source line.
    Cython embeds comments like: /* "randovania/_native.py":1378
    """
    if not cpp_file.exists() or not cpp_file.suffix == ".cpp":
        return None

    try:
        with cpp_file.open() as f:
            # Read a window of lines around the target
            start_line = max(1, cpp_line - context_lines)
            end_line = cpp_line + 1

            f.seek(0)
            for _ in range(start_line - 1):
                f.readline()

            lines_to_check = []
            for i in range(start_line, end_line + 1):
                line = f.readline()
                if not line:
                    break
                lines_to_check.append((i, line))

            # Search backwards from the target line for the most recent Python line comment
            # Pattern: /* "path/to/file.py":line_number
            pattern = re.compile(r'/\*\s*"([^"]+\.py)":(\d+)')

            for line_num, line_content in reversed(lines_to_check):
                match = pattern.search(line_content)
                if match:
                    py_file = match.group(1)
                    py_line = int(match.group(2))
                    return (py_file, py_line)

    except Exception:
        pass

    return None


def cmd_check_function(args):
    """Analyze where time is spent in a specific function."""
    raw_file = args.raw_file
    function_name = args.function_name

    print(f"Analyzing '{raw_file}' for function '{function_name}'...")
    print()

    # Parse the raw profile
    file = raw_file.open() if raw_file.name != "-" else sys.stdin
    traces = parse_raw_profile(file)
    print(f"Total samples in profile: {len(traces)}")

    # Extract traces containing the function
    function_traces = extract_function_samples(traces, function_name)
    print(f"Samples in '{function_name}': {len(function_traces)}")

    if not function_traces:
        print(f"\nNo samples found for function '{function_name}'")
        return

    percentage = (len(function_traces) / len(traces)) * 100
    print(f"Percentage: {percentage:.1f}%")
    print()

    # Analyze where time is spent within the function
    line_counts = analyze_function_hotspots(function_traces, function_name)

    # Group by line number for same function
    line_number_counts = defaultdict(int)
    frame_by_line = {}

    for frame, count in line_counts.items():
        func, file, line = format_frame(frame)
        if line and function_name in func:
            key = f"{file}:{line}"
            line_number_counts[key] += count
            if key not in frame_by_line:
                frame_by_line[key] = frame

    # Sort by count (descending) and by line number (ascending)
    sorted_by_count = sorted(line_number_counts.items(), key=lambda x: x[1], reverse=True)

    print("=" * 80)
    print(f"Time Distribution in '{function_name}'")
    print("=" * 80)
    print()

    print(f"{'Samples':<10} {'%':<8} {'Location'}")
    print("-" * 80)

    # Get top 30 by count, then sort those by line number
    top_30_by_count = sorted_by_count[:30]
    top_30_sorted_by_line = sorted(top_30_by_count, key=lambda x: int(x[0].rsplit(":", 1)[1]) if ":" in x[0] else 0)

    for location, count in top_30_sorted_by_line:
        pct = (count / len(function_traces)) * 100
        print(f"{count:<10} {pct:>6.1f}%  {location}")

    print()
    print("=" * 80)
    print("Top Bottlenecks (by sample count):")
    print("=" * 80)

    # Show top 10 with full frame information
    for i, (location, count) in enumerate(sorted_by_count[:10], 1):
        pct = (count / len(function_traces)) * 100
        frame = frame_by_line.get(location, location)

        # Try to map C++ lines back to Python source
        file_part, line_part = location.rsplit(":", 1)
        python_info = ""
        if file_part.endswith(".cpp"):
            cpp_file = Path(file_part).resolve() if Path(file_part).is_absolute() else Path.cwd() / file_part
            py_mapping = map_cpp_to_python_line(cpp_file, int(line_part))
            if py_mapping:
                py_file, py_line = py_mapping
                python_info = f" (Python: {py_file}:{py_line})"

        print(f"\n{i}. Line {location.split(':')[-1]} - {count} samples ({pct:.1f}%){python_info}")
        print(f"   {frame}")


# ============================================================================
# CHART COMMAND - Generate function statistics chart
# ============================================================================


def extract_function_name(frame: str) -> str:
    """
    Extract function name from frame string.
    Format: {name} ({file}:{line})
    Function name is: {file}:{name}
    """
    func, file, line = format_frame(frame)
    if file:
        return f"{file}:{func}"
    return func


def cmd_chart(args):
    """Generate statistics chart for all functions in the profile."""
    raw_file = args.raw_file

    # Parse the raw profile
    file = raw_file.open() if raw_file.name != "-" else sys.stdin
    traces = parse_raw_profile(file)
    print(f"Total samples in profile: {len(traces)}")
    print()

    # Statistics tracking
    appears_in_trace = Counter()  # How many traces contain this function
    last_frame_all = Counter()  # How many times this function is the last frame
    last_frame_randovania = Counter()  # How many times it's last frame and belongs to randovania/

    for trace in traces:
        # Track unique functions in this trace
        functions_in_trace = set()

        for frame in trace:
            func_name = extract_function_name(frame)
            functions_in_trace.add(func_name)

        # Count appearances
        for func_name in functions_in_trace:
            appears_in_trace[func_name] += 1

        # Check last frame
        if trace:
            last_frame = trace[-1]
            func_name = extract_function_name(last_frame)
            last_frame_all[func_name] += 1

        # Check last frame that belongs to randovania/
        for frame in reversed(trace):
            _, file, _ = format_frame(frame)
            if file.startswith("randovania/"):
                func_name = extract_function_name(frame)
                last_frame_randovania[func_name] += 1
                break

    # Sort by selected column
    if args.sort_by == "last-frame":
        sorted_functions = sorted(last_frame_all.items(), key=lambda x: x[1], reverse=True)
    elif args.sort_by == "last-randovania":
        sorted_functions = sorted(last_frame_randovania.items(), key=lambda x: x[1], reverse=True)
    else:  # "in-trace"
        sorted_functions = sorted(appears_in_trace.items(), key=lambda x: x[1], reverse=True)

    # Export to CSV if requested
    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Function", "In Trace", "Last Frame", "Last (randovania/)"])

            for func_name, appears_count in sorted_functions:
                last_all = last_frame_all.get(func_name, 0)
                last_rando = last_frame_randovania.get(func_name, 0)
                writer.writerow([func_name, appears_count, last_all, last_rando])

        print(f"Data exported to: {args.csv}")
        return

    # Calculate the maximum function name length for alignment
    display_functions = sorted_functions[:50]  # Show top 50
    if args.no_truncate:
        max_name_len = max(len(func_name) for func_name, _ in display_functions)
    else:
        max_name_len = min(60, max(len(func_name) for func_name, _ in display_functions))

    # Ensure minimum width for header
    max_name_len = max(max_name_len, len("Function"))

    print(f"{'Function':<{max_name_len}} {'In Trace':<12} {'Last Frame':<12} {'Last (randovania/)':<12}")
    print("-" * (max_name_len + 12 + 12 + 12 + 3))

    for func_name, appears_count in display_functions:
        last_all = last_frame_all.get(func_name, 0)
        last_rando = last_frame_randovania.get(func_name, 0)

        # Truncate long function names unless --no-truncate is set
        if args.no_truncate:
            display_name = func_name
        else:
            display_name = func_name if len(func_name) <= 60 else func_name[:57] + "..."

        print(f"{display_name:<{max_name_len}} {appears_count:<12} {last_all:<12} {last_rando:<12}")


# ============================================================================
# MAIN - Command router
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Unified tool for working with py-spy profiler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to execute")

    # COLLECT subcommand
    collect_parser = subparsers.add_parser(
        "collect", help="Profile a Python process with py-spy", formatter_class=argparse.RawDescriptionHelpFormatter
    )
    collect_parser.add_argument(
        "-o", "--output", default="profile_native.svg", help="Output file (default: profile_native.svg)"
    )
    collect_parser.add_argument("-r", "--rate", type=int, default=100, help="Sampling rate in Hz (default: 100)")
    collect_parser.add_argument(
        "-f",
        "--format",
        choices=["flamegraph", "raw", "speedscope"],
        default="flamegraph",
        help="Output format (default: flamegraph)",
    )
    collect_parser.add_argument("python_command", nargs="+", help="Command and arguments to pass to Python")

    # FILTER subcommand
    filter_parser = subparsers.add_parser("filter", help="Filter py-spy raw output to remove noise")
    filter_parser.add_argument("raw_file", type=Path, help="Path to the py-spy raw profile file (or - for stdin)")
    filter_parser.add_argument("--keep-frozen", action="store_true", help="Keep <frozen> frames (default: exclude)")
    filter_parser.add_argument("--keep-asyncio", action="store_true", help="Keep asyncio frames (default: exclude)")
    filter_parser.add_argument(
        "--keep-python-api", action="store_true", help="Keep Python C API frames (default: exclude)"
    )
    filter_parser.add_argument(
        "--keep-python-exe", action="store_true", help="Keep python.exe frames (default: exclude)"
    )

    # CHECK-FUNCTION subcommand
    check_parser = subparsers.add_parser("check-function", help="Analyze where time is spent in a specific function")
    check_parser.add_argument("raw_file", type=Path, help="Path to the py-spy raw profile file (or - for stdin)")
    check_parser.add_argument("function_name", help="Name of the function to analyze")

    # CHART subcommand
    chart_parser = subparsers.add_parser("chart", help="Generate function statistics chart from raw profile")
    chart_parser.add_argument("raw_file", type=Path, help="Path to the py-spy raw profile file (or - for stdin)")
    chart_parser.add_argument("--csv", type=Path, help="Export data to CSV file")
    chart_parser.add_argument(
        "--sort-by",
        choices=["in-trace", "last-frame", "last-randovania"],
        default="in-trace",
        help="Column to sort by (default: in-trace)",
    )
    chart_parser.add_argument(
        "--no-truncate",
        action="store_true",
        help="Don't truncate long function names in console output",
    )

    args = parser.parse_args()

    # Route to appropriate command
    if args.command == "collect":
        cmd_collect(args)
    elif args.command == "filter":
        # Invert the keep flags to exclude flags
        args.exclude_frozen = not args.keep_frozen
        args.exclude_asyncio = not args.keep_asyncio
        args.exclude_python_api = not args.keep_python_api
        args.exclude_python_exe = not args.keep_python_exe
        cmd_filter(args)
    elif args.command == "check-function":
        cmd_check_function(args)
    elif args.command == "chart":
        cmd_chart(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
