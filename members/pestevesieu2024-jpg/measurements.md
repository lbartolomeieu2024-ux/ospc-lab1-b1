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

## 5.2 Task 1: report.py alone
- python3 steps/report.py: Killed, echo $? = 137 (128 + 9, SIGKILL)
- memory.events after (fresh container): oom 1, oom_kill 1, max 579

| Orders | Table (printed) | Elapsed | User | System | Peak memory |
|---|---|---|---|---|---|
| 1,000,000 | 106 MiB | 2.24 s | 2.32 s | 0.33 s | 510372 KB |
| 2,000,000 | 211 MiB | 3.83 s | 3.93 s | 0.52 s | 856256 KB |
| 4,000,000 | 423 MiB | 7.16 s | 6.78 s | 0.98 s | 1568916 KB |
| 8,400,000 | 887 MiB | killed | | | ~2090000 KB |
- Peak grows linearly, ~356000 KB per million orders + ~144000 KB fixed
- Estimate for 8.4M: ~3140000 KB (~3.0 GiB), limit 2 GiB
- With | tee: log empty, no "loaded" line; PIPESTATUS = 137 0

## 5.3 Task 2: extracts
- bash steps/extracts.sh: prints "extracts: done", echo $? = 0, all 6 files 0 bytes
- Script does cd "$OUT/extracts", then reads ../data/sales_2025.csv
- From there that path is /home/analyst/data/out/data/sales_2025.csv (does not exist)
- Manual pipeline without 2>/dev/null: "grep: ../data/sales_2025.csv: No such file or directory", wc -l = 0
- PIPESTATUS = 2 0 0 (grep failed, cut and wc succeeded)

## 5.4 Task 3: audit
| Data | Orders | Elapsed | User | System | Peak memory |
|---|---|---|---|---|---|
| sample | 100,000 | 1.57 s | 1.57 s | 0.38 s | 127848 KB |
| full | 8,400,000 | 80.45 s | 60.88 s | 20.16 s | 634500 KB |
- Full file: system = 20.16 / 81.04 s CPU = ~25% (report.py on 4M orders: ~13%)
- strace -c on the sample: openat 100686 (13 errors), write 100001, close 100673, total 301360
- audit_2025.csv on the sample: 1952269 bytes
- Single open file with a 128 KiB buffer: ~15 writes instead of 100000
