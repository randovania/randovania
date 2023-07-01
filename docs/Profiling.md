
Here's a list of profilers one can use with Randovania:

## pyinstrument

### Source
https://github.com/joerick/pyinstrument

### Install
`python -m pip install pyinstrument`

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
`python -m pip install viztracer`

### Profile Usage 
```python
with VizTracer(output_file="viz_tracer_report.json") as tracer:
    # Something happens here
```

### View Report 
`vizviewer viz_tracer_report.json`

This opens a webui with your browser. Only compatible with Chromium based browser, but Edge works.

## py-spy

Sampling profiler, can profile already running processes. Not compatible with Python 3.11.

### Source
https://github.com/benfred/py-spy

### Install
`python -m pip install py-spy`
