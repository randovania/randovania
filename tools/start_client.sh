#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

uv run randovania gui main
