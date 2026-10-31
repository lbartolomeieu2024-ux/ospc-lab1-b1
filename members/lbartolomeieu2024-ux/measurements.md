
## Task 2: extracts.sh

- `grep ",Iberia," ../data/sales_2025.csv | ...` from `~/data/out/extracts`: `grep: No such file or directory`, `0`. `echo ${PIPESTATUS[@]}`: `2 0 0`.
- Correct path (`grep ",Iberia," ~/data/sales_2025.csv | wc -l`): `2183057` lines, `echo ${PIPESTATUS[@]}`: `0 0`.
- After the fix, full run of `bash steps/extracts.sh`: 4.08 s elapsed, 4.95 s user, 1.10 s system, 8,576 KB peak memory. Six files with 8,400,000 rows in total.

## Task 3: audit.py (sample of 100,000 orders, `strace -c -e trace=openat,write,close`)

| Syscall | Original | Fixed (file opened once) |
|---|---|---|
| openat | 100689 (17 errors) | 691 (17 errors) |
| write | 100001 | 17 |
| close | 100677 | 679 |
| total | 301367 | 1387 |

- Fixed version, full file (8.4 million orders): 23.24 s elapsed, 635,248 KB peak memory.

## Task 1: report.py memory (`/usr/bin/time`, DATA = head of the file)

| Orders | File (MiB) | Elapsed (s) | User (s) | System (s) | Peak memory (KB) | Exit |
|---|---|---|---|---|---|---|
| 1,000,000 | 106 | 3.75 | 4.32 | 0.80 | 508,156 | 0 |
| 2,000,000 | 211 | 4.55 | 5.91 | 0.80 | 855,736 | 0 |
| 4,000,000 | 423 | 8.61 | 8.93 | 1.47 | 1,571,064 | 0 |
| 8,400,000 | 887 | — | — | — | over 2,097,152 | 137 (killed) |

- Memory grows linearly: about 354,302 KB per million orders plus about 153,854 KB of base memory. The full file needs about 3 GB, more than the 2 GB limit.
