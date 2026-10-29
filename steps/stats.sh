#!/bin/bash
# Bootstrap 95% confidence intervals for the average order value of every
# region and month. The work is split among WORKERS processes that run at
# the same time: more workers, faster results.

WORKERS=${WORKERS:-$(nproc)}
OUT=${OUT:-$HOME/data/out}

python3 steps/stats_prepare.py
mkdir -p "$OUT/stats"
rm -f "$OUT"/stats/part_*.csv
pids=()
trap 'echo "stats: interrupted, stopping workers" >&2; kill "${pids[@]}" 2>/dev/null; wait; exit 130' INT TERM
for k in $(seq 0 $((WORKERS - 1))); do
    python3 steps/stats_worker.py "$k" "$WORKERS" &
    pids+=($!)
done
wait
cat "$OUT"/stats/part_*.csv | sort > "$OUT/stats.csv"
echo "stats: done with $WORKERS workers"
