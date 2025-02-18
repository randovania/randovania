#!/usr/bin/env bash

set -e -x
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.."

if [ ! -d "./.git" ]; then
    echo ""
    echo "Downloading Randovania via the \"Download ZIP\" button in GitHub is not supported."
    echo ""
    echo "Please follow the instructions in the README:"
    echo "  https://github.com/randovania/randovania/blob/main/README.md#installation"
    echo ""
    read -p "Press enter to exit."
    exit
fi

if [ "$1" == "--all" ]; then
    extra_arg=(--all-extras)
else
    extra_arg=(--extra gui)
fi

uv sync --frozen "${extra_arg[@]}"
uvx pre-commit install

echo "Setup finished successfully."
