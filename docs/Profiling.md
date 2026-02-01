
Here's a list of profilers one can use with Randovania:

## py-spy

Sampling profiler, can profile already running processes. Recommended for use.

### Source
https://github.com/benfred/py-spy

### Install
`uv pip install py-spy`

### Usage

The script `tools/pyspy_tools.py` contains many helper tools for making the use of py-spy easier and faster.

#### Collecting a sample

For profiling generating a game, you can use this for example:

```shell
python tools/pyspy_tools.py collect -o profile.raw -- -m randovania layout generate-from-presets --name "dread/Starter Preset" --development --seed-number 0 --no-validate out.rdvgame
```
This creates a trace file named `profile.raw`, by pausing the process 100 times per second (configurable via `--rate`)
and recording the process stack. This file is hard to use manually, but it's useful for the other commands.

#### Making Reports

The `chart` command makes a report on the functions that show up the most in the trace file.
```shell
python tools/pyspy_tools.py chart profile.raw
```
For each function, we get the number of traces it shows up, the number of times it's the end of a trace, and
the number of times it's the last Randovania function in the trace. By default, it sorts by end-of-trace count.

Good arguments:
* `--filter`: removes many traces from the file that are unlikely to be helpful.
* `--no-truncate`: show the full function name, even if too big
* `--csv <path>`: create a CSV file with the full data, if you'd like to use a different program to look at data.

The `check-function` command gives more details on a specific function.
```shell
python tools/pyspy_tools.py check-function profile.raw _calculate_safe_nodes
```
It calculates the percentage of time that is spent in each line of the function, based on how many traces include that exact line.
Running this command from the VS Code terminal is extra nice, as it turns the file name + line number printed into
something you can Ctrl + Click to open your editor in the mentioned line, making it easy to see what's going on.

#### Flamegraphs

Flamegraphs are very popular and good way to visualize trace files. See [official website](https://www.brendangregg.com/flamegraphs.html)
for them for more details.

`py-spy` can create flamegraphs directly. Using `python tools/pyspy_tools.py collect -f flamegraph -o profile.svg -- ...` will create one,
however you can't use the other commands instead.

For creating a flamegraph out of the trace file, you can use [inferno](https://crates.io/crates/inferno) instead.
First install via `cargo install inferno` (read [this](https://doc.rust-lang.org/cargo/getting-started/installation.html) to install cargo),
then run `python tools/pyspy_tools.py flamegraph --filter profile.raw -o profile.svg`.


## pyinstrument

### Source
https://github.com/joerick/pyinstrument

### Install
`uv pip install pyinstrument`

### Profile Usage
1. `pyinstrument -m randovania ...`
2. `pyinstrument -m pytest ...`

### View Report

1. Prints on console by default
2. Re-export a previous report with `pyinstrument --load-prev <...> -o report.html`


## viztracer

Shows function time over a timeline.

### Source
https://github.com/gaogaotiantian/viztracer

### Install
`uv pip install viztracer`

### Profile Usage
```python
with VizTracer(output_file="viz_tracer_report.json") as tracer:
    # Something happens here
```

### View Report
`vizviewer viz_tracer_report.json`

This opens a webui with your browser. Only compatible with Chromium based browser, but Edge works.
