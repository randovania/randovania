#!/usr/bin/env python3
"""
Analyze py-spy raw format profile data to show where time is spent in a specific function.

Usage:
    python analyze_pyspy_raw.py <raw_file> <function_name>

Example:
    python analyze_pyspy_raw.py after3.raw resolver_reach_process_nodes
"""

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


def parse_raw_profile(filepath: Path) -> list[list[str]]:
    """Parse a py-spy raw format file into a list of stack traces."""
    traces = []
    with filepath.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Each line is: frame1;frame2;frame3;... count
            # Split by space to separate stack from count
            parts = line.rsplit(" ", 1)
            if len(parts) != 2:
                continue
            stack_str, count_str = parts
            try:
                count = int(count_str)
            except ValueError:
                continue

            # Split the stack trace by semicolon
            frames = stack_str.split(";")
            # Add this trace 'count' times (usually just 1)
            for _ in range(count):
                traces.append(frames)

    return traces


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


def main():
    if len(sys.argv) != 3:
        print("Usage: python analyze_pyspy_raw.py <raw_file> <function_name>")
        print("\nExample:")
        print("    python analyze_pyspy_raw.py after3.raw resolver_reach_process_nodes")
        sys.exit(1)

    raw_file = Path(sys.argv[1])
    function_name = sys.argv[2]

    if not raw_file.exists():
        print(f"Error: File '{raw_file}' not found")
        sys.exit(1)

    print(f"Analyzing '{raw_file}' for function '{function_name}'...")
    print()

    # Parse the raw profile
    traces = parse_raw_profile(raw_file)
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


if __name__ == "__main__":
    main()
