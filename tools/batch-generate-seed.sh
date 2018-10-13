#!/bin/bash

set -e

if [ "$#" -ne 3 ]; then
	echo "Usage: $0 starting_seed seed_count output_dir"
	exit 1
fi

starting_seed=$1
seed_count=$2
output_dir="$3"

mkdir -p "$output_dir"

if [ ! -f randovania/__main__.py ]; then
	echo "Randovania not found in current dir"
	exit 2
fi

typeset -i seed
let seed=$starting_seed
for ((i=1;i<=$seed_count;i++)); do
	python -m randovania echoes distribute --logic hard --seed $seed "$output_dir/$seed.json" &
	let seed++
done

wait
