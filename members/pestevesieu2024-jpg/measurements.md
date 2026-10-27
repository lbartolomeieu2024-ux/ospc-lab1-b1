# Measurements of pestevesieu2024-jpg
Apple MacBook Pro 13-inch M1 2020, macOS Tahoe 26.6.2, nproc 8

## 5.1 Warm-up
- ./run_report.sh: "bad interpreter: Permission denied"
- ls -l before: -rw-r--r--   after chmod +x: -rwxr-xr-x
- bash run_report.sh works

## 5.2 Task 1: full pipeline, /usr/bin/time
| Run | Elapsed | User | System | Peak memory |
|---|---|---|---|---|
| 1 | 152.78 s | 196.26 s | 27.61 s | 2090408 KB |
| 2 | 151.97 s | 195.52 s | 26.93 s | 2090196 KB |
- report.py: "loaded 8,400,000 orders (887 MiB)", then Killed, in every run
- memory.events before the timed runs: oom 2, oom_kill 2
- extracts/*.csv: all 6 files are 0 bytes
