#!/bin/bash
# change_freq.sh
# Thay đổi chu kì X trong file freq.txt mỗi 1 phút
# Thứ tự: 1000000 ns → 100000 ns → 10000 ns → 1000 ns → 100 ns

FREQ_FILE="freq.txt"
PERIODS=(1000000 100000 10000 1000 100)
LABELS=("1 ms (1,000,000 ns)" "100 µs (100,000 ns)" "10 µs (10,000 ns)" "1 µs (1,000 ns)" "100 ns")

echo "[SCRIPT] Starting frequency changer. Will update every 60 seconds."
echo "[SCRIPT] Total duration: 5 minutes (5 periods × 1 minute)"

for i in "${!PERIODS[@]}"; do
    echo "[SCRIPT] Setting period = ${LABELS[$i]}"
    echo "${PERIODS[$i]}" > "$FREQ_FILE"
    sleep 60
done

echo "[SCRIPT] All periods done. Stopping C program..."
pkill -INT -f timer_threads || pkill -INT sudo trong change_freq.sh 2>/dev/null || true
echo "[SCRIPT] Done."