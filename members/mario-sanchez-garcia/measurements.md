# Measurements - mario-sanchez-garcia
Laptop: Apple MacBook Pro 14-inch Nov 2023 M3, macOS Sonoma 14.2, container: 8 CPUs, 2 GiB memory limit

## 5.1 Warm-up
run_report.sh was -rw-r--r-- (no x): ./run_report.sh gave "Permission denied". Fixed with chmod +x.

## 5.2 Task 1: report.py killed (memory)
- Whole pipeline: 204.37 s elapsed, 234.08 s user, 46.70 s system, 2085192 KB peak
- report.py on the whole file: exit status 137 (SIGKILL), memory.events: oom_kill 2, memory.max = 2147483648 (2 GiB)

| Orders | Table (MiB) | Elapsed (s) | User (s) | System (s) | Peak memory (KB) |
|---|---|---|---|---|---|
| 1,000,000 | 106 | 4.44 | 3.22 | 1.76 | 506144 |
| 2,000,000 | 211 | 6.35 | 5.03 | 1.92 | 855836 |
| 4,000,000 | 423 | 14.87 | 11.13 | 4.34 | 1568468 |
| 8,400,000 (estimate) | 887 | - | - | - | about 3 GiB |

With tee, "report: loaded" is missing from the log: Python buffers stdout when it is a pipe and the OOM killer (SIGKILL) gives no chance to flush.

## 5.3 Task 2: extracts.sh
All 6 files are empty (0 bytes). The script does cd into ~/data/out/extracts, so ../data/sales_2025.csv is ~/data/out/data/sales_2025.csv, which does not exist. grep fails (status 2) but PIPESTATUS is "2 0 0", so the pipeline returns 0 and the script prints done. 2>/dev/null hides the grep error.

## 5.4 Task 3: audit.py
- Sample (100,000 orders): 4.29 s elapsed, 2.45 s user, 2.22 s system, 127884 KB peak
- Whole file (8.4M orders): 105.60 s elapsed, 68.53 s user, 35.27 s system (34% of CPU in the kernel), 643288 KB peak
- strace on the sample: openat 100686 (13 errors), write 100001, close 100673
- The file is opened and closed for every order. close does not force data to disk (only fsync does).
- With one open file and a 128 KiB buffer: about 1952269 / 131072 = 15 write calls.
