#!/usr/bin/env bash

set -e -x
this_dir="$( dirname -- "${BASH_SOURCE[0]}" )"

TARGET_GAME=${TARGET_GAME:-dread}
TARGET_PRESET=${TARGET_PRESET:-Starter Preset}
TARGET_SEED_COUNT=${TARGET_SEED_COUNT:-100}
PROCESS_COUNT=${PROCESS_COUNT:-6}

OUTPUT_PATH=${OUTPUT_PATH:-${this_dir}/bulk}
RDVGAME_PATH=${RDVGAME_PATH:-${OUTPUT_PATH}/rdvgame}
REPORT_PATH=${REPORT_PATH:-${OUTPUT_PATH}/report.json}
GENERATION_LOG_PATH=${GENERATION_LOG_PATH:-${OUTPUT_PATH}/generation.log}
: "${WEBHOOK_URL:?Variable not set or empty}"

# Get permalink
permalink=$(python -m randovania layout permalink --game "${TARGET_GAME}" --preset-name "${TARGET_PRESET}" --seed-number 1000 --development)

# Delete old path
rm -rf "$OUTPUT_PATH"
mkdir -p "$OUTPUT_PATH"

# Batch generate
python -m randovania layout batch-distribute --process-count "${PROCESS_COUNT}" "$permalink" "${TARGET_SEED_COUNT}" "$RDVGAME_PATH" | tee "$GENERATION_LOG_PATH"
generated_count=$(find "$RDVGAME_PATH/" -type f | wc -l)
failed_count=$((TARGET_SEED_COUNT - generated_count))
timed_out_count=$(grep -c "Timeout reached when validating possibility" "$GENERATION_LOG_PATH")

# Analyze
python tools/log_analyzer.py "$RDVGAME_PATH" "$REPORT_PATH"


# Pack everything
rm -f games.tar.gz
tar czvf games.tar.gz "$RDVGAME_PATH" "$REPORT_PATH" "$GENERATION_LOG_PATH"

# Send report
python tools/send_report_to_discord.py \
    --title "Batch report for ${TARGET_GAME}" \
    --field "Generated:${generated_count} out of ${TARGET_SEED_COUNT}" \
    --field "Timed out:${timed_out_count} out of ${failed_count} failures" \
    --field "Preset:${TARGET_PRESET}" \
    --attach games.tar.gz \
    --webhook "${WEBHOOK_URL}"