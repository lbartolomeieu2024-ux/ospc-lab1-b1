# Lab 1 - The Nightly Report
Salim Cherraj - saL1mZzz

These notes distinguish my own terminal measurements from diagnoses
documented by teammates. Task 2 and Task 3 were already fixed when
I measured them in this session.

## Section 5.1 - Warm-up: Generating the report

### My observations

./run_report.sh started successfully. The permissions were:

-rwxr-xr-x 1 analyst analyst 402 Oct 27 16:30 run_report.sh

The pipeline printed "report: loaded 8,400,000 orders (887 MiB)",
then report.py was killed. The remaining steps continued, and the
pipeline printed "Nightly report finished".

### Answers

1. With permissions -rw-r--r--, execute permission is missing for
   the owner, group and others. My copy already had execute permission
   for all three, so I did not encounter "Permission denied".

2. bash run_report.sh works without execute permission on the script
   because Bash reads and interprets its contents. Read permission
   on the script is still required.

3. The team report records -rw-r--r-- on Pablo's copy, whereas mine
   showed -rwxr-xr-x. chmod +x run_report.sh adds execute permission.
   Git can record and share the executable-bit change. Permissions
   inside Docker also depend on the host filesystem and mount settings;
   they should be compared from actual ls -l outputs.

## Section 5.2 - Task 1: Generating the report again

### My observations

The full pipeline continued after report.py was killed.
Running python3 steps/report.py separately produced:

report: loaded 8,400,000 orders (887 MiB)
Killed

echo $? returned 137.

My container's memory limit was 2147483648 bytes (2 GiB).
The memory.events output was:

low 0
high 0
max 14503
oom 3
oom_kill 3
oom_group_kill 0
sock_throttled 0

These counters accumulate during the container's lifetime.
I did not capture a before-and-after counter comparison for this run.

### My measured results

Timing format:
T='%e s elapsed, %U s user, %S s system, %M KB peak memory'

I generated subsets with head, including one extra line for the header,
then ran steps/report.py with DATA pointing to each subset and OUT=/tmp.

| Orders | Table (MiB) | Elapsed (s) | User (s) | System (s) | Peak memory (KB) |
|---|---:|---:|---:|---:|---:|
| 1,000,000 | 106 | 3.58 | 1.82 | 1.39 | 511336 |
| 2,000,000 | 211 | 3.84 | 3.05 | 1.04 | 856428 |
| 4,000,000 | 423 | 7.86 | 5.80 | 2.31 | 1566608 |

All three subset runs printed "report: done".

### Answers

1. Exit status 137 is 128 + 9, indicating termination by SIGKILL.
   The nonzero oom_kill counter shows that the kernel's OOM killer
   killed processes in this container. Together with the observed
   memory growth and 2 GiB limit, this supports the OOM diagnosis.
   Exit status 137 alone does not establish who sent SIGKILL.

2. The reported 887 MiB describes the table, not the process's total
   peak memory. Python, intermediate objects and temporary allocations
   require additional memory. The cgroup limit also applies to the
   container's processes together.

3. Peak memory grows approximately linearly with the number of orders.
   Between 2 and 4 million orders, the increase per million is:

   (1566608 - 856428) / 2 = 355090 KB per million orders.

   Extrapolating from 4 million to 8.4 million:

   1566608 + 4.4 * 355090 = 3129004 KB, approximately 2.98 GiB.

   This is an estimate, not a measured full-file peak. It exceeds
   the container's 2 GiB limit.

4. I ran:
   python3 steps/report.py | tee /tmp/report.log
   cat /tmp/report.log

   The log was empty. When stdout goes to a pipe, Python normally
   buffers its output. If SIGKILL arrives before that buffer is
   flushed, the "loaded" message never reaches tee.
   SIGKILL cannot be caught to flush the buffer before exiting.

### Remaining work

Memory fix and verification

I changed report.py to read only order_date, region, quantity and
unit_price, and group the orders directly by region and month.
This removes the twelve monthly subsets and the concatenated copy.
I also added flush=True so the progress message is flushed immediately.

Full-file results after the fix:

Orders: 8,400,000

Loaded table: 382 MiB

Elapsed: 8.45 s

User CPU: 7.54 s

System CPU: 1.15 s

Peak memory: 1,259,504 KB

Exit status: 0

Verification: PASS revenue_by_region_month.csv

The original full run was killed. Its full-run peak memory and timing
were not captured, so I cannot calculate a measured speedup or exact
peak-memory reduction.

## Section 5.3 - Task 2: Extracting data

### Original fault: explanation from the team's documented diagnosis

1. The original script changed into ~/data/out/extracts and then used
   ../data/sales_2025.csv. From that directory, the path resolves to:

   /home/analyst/data/out/data/sales_2025.csv

   The intended input is /home/analyst/data/sales_2025.csv.
   The shell creates or truncates output files for redirection even
   when grep cannot read the input, leaving empty files.

2. Without pipefail, a pipeline normally returns the status of its
   last command. In the original script, that command was cut.
   In the handout's diagnostic pipeline, it was wc -l.
   These commands can succeed even when grep fails. The script then
   runs its final echo, prints "extracts: done", and exits with 0.

3. 2>/dev/null attached to grep discards grep's standard error,
   including "No such file or directory". It does not suppress
   standard error from cut, mkdir or other separate commands.

4. set -e exits on an unhandled failing command, subject to Bash's
   exceptions, such as commands used as conditional tests.
   set -u reports an error for expansion of unset variables.
   set -o pipefail makes a pipeline return its rightmost nonzero
   command status, or 0 if all commands succeed.
   Combining -e and pipefail makes this script stop when grep fails.
   Removing 2>/dev/null makes the diagnostic visible.

### Current code and my verification

The script already contained the team's fix:
- set -euo pipefail
- Input read from "$DATA"
- Output written to "$OUT/extracts/$region.csv"
- No directory change or suppression of grep errors

My run printed "extracts: done" and returned exit status 0.
All six files were nonempty and passed tools/check.py:

| Region | Rows |
|---|---:|
| Benelux | 1006912 |
| DACH | 1846894 |
| France | 1345118 |
| Iberia | 2183057 |
| Italy | 1178032 |
| Nordics | 839987 |
| Total | 8400000 |

I did not measure extraction timings or personally reproduce the
original failure in this session. The original failure evidence and
before/after timings in REPORT.md belong to the teammate who ran them.

## Section 5.4 - Task 3: Auditing

### Code inspected

The current script keeps the output file open around the entire loop:

with open(path, "w") as f:
    for order in orders.itertuples():
        f.write(...)

The team's fix was already present before my measurements.
There is also a redundant open(path, "w").close() before this block.
I did not change the script.

### My fixed-version timings

Commands used:

DATA="$HOME/data/sales_2025_sample.csv" OUT=/tmp/salim-audit-sample /usr/bin/time -f "$T" python3 steps/audit.py

DATA="$HOME/data/sales_2025.csv" OUT="$HOME/data/out" /usr/bin/time -f "$T" python3 steps/audit.py

| Dataset/run | Elapsed (s) | User (s) | System (s) | Peak memory (KB) | Exit |
|---|---:|---:|---:|---:|---:|
| 100,000 orders | 0.41 | 0.59 | 0.07 | 130256 | 0 |
| 8,400,000 orders, run 1 | 13.15 | 12.89 | 0.52 | 633876 | 0 |
| 8,400,000 orders, run 2 | 11.56 | 11.37 | 0.45 | 634852 | 0 |

Both full runs printed "audit: 8,400,000 lines written".
The latest full audit output passed tools/check.py with 8400000 lines.

### My sample system-call measurements

Command:

DATA="$HOME/data/sales_2025_sample.csv" OUT=/tmp/salim-audit-sample strace -c -e trace=openat,write,close python3 steps/audit.py

| System call | Calls | Errors |
|---|---:|---:|
| openat | 687 | 13 |
| write | 17 | 0 |
| close | 674 | 0 |
| Total | 1378 | 13 |

The command returned 0. The sample output was 1952269 bytes.
These counts cover the whole program, including imports and printing;
the summary does not identify the cause of the 13 openat errors.

### Answers

1. My fixed version made 687 openat, 17 write and 674 close calls.
   The original per-order open/write/close behavior, documented by
   the team, caused roughly 100000 of each call on the sample.
   Keeping the file open allows buffering and avoids that repeated
   per-order overhead. I did not measure the original audit version.

2. In my second full run, user CPU time was 11.37 s and system CPU
   time was 0.45 s. The system share of total CPU time was:

   0.45 / (11.37 + 0.45) * 100 = 3.8%.

   The first full run also had a system share of approximately 3.9%.
   Most CPU time in the fixed audit was spent in user code.

   For comparison, my 4-million-order report.py run had a system
   share of 2.31 / (5.80 + 2.31) * 100 = 28.5%.
   This comparison uses different dataset sizes and different steps;
   I have no successful full-file report.py timing for a direct
   comparison. CPU-time shares alone do not count system calls.

3. Opening and closing a file for every order does not guarantee
   physical disk storage. Closing flushes Python's buffered data to
   the operating system, which may retain it in its page cache.
   A durability request such as fsync is a separate operation.

4. Assuming a 128 KiB buffer:

   128 * 1024 = 131072 bytes.
   ceil(1952269 / 131072) = approximately 15 file writes.

   The measured whole-program count was 17 writes. The estimate
   does not include all other writes or buffering details.
   A detailed trace would be needed to identify each write precisely.

Task 4 - Segmenting the orders

Code and diagnosis

The team's optimization was already present when I ran this task.
The script converts the whole order_date column to quarters before
the loop. segment() reads the precomputed quarter, classifies the
order value, and returns the segment label.

The team documented repeated per-order date parsing as the original
bottleneck. I inspected and measured the fixed version; I did not
personally measure the original version.

My full-dataset measurements

Command:
DATA="$HOME/data/sales_2025.csv" OUT="$HOME/data/out" /usr/bin/time -f "$T" python3 steps/segments.py

Elapsed: 18.43 s

User CPU: 17.86 s

System CPU: 0.79 s

Peak memory: 1265336 KB

Exit status: 0

User time accounted for 17.86 / (17.86 + 0.79) * 100 = 95.8%
of CPU time. This motivated inspecting Python execution with cProfile.

My sample profile

Command:
DATA="$HOME/data/sales_2025_sample.csv" OUT=/tmp/salim-segments-sample python3 -m cProfile -s tottime steps/segments.py

Total calls: 1152309

Primitive calls: 1139923

Profiled duration: 0.587 s

segment(): 100000 calls, 0.019 s internal and cumulative time

array.py iter(): 200514 calls, 0.097 s internal time

Exit status: 0

segment() still runs once per order, but no longer parses dates.
Array iteration was the largest individual entry in the displayed
profile sorted by internal time.

Profiling adds overhead; its duration is not a normal timing result.
Without my own original-version measurements, I cannot claim a
personal speedup or measured memory increase.

Verification

tools/check.py returned PASS segments.csv after my full run.


## Task 5 - Computing the statistics

### Current implementation

The team's fixes were already present when I inspected stats.sh.
WORKERS defaults to nproc, unless explicitly overridden.
The script records worker PIDs and installs a handler for SIGINT
and SIGTERM that sends termination signals to the workers,
waits for them, and exits with status 130.

### My interruption test

Before testing, no stats_worker.py processes were found.
WORKERS was unset and nproc returned 4.

Command:
OUT=/tmp/salim-stats-interrupt bash steps/stats.sh

My first attempt finished before I pressed Ctrl-C, so it did not
test interruption. On the second attempt, I pressed Ctrl-C while
the script was running after "stats: input ready".

Observed:
- Message: "stats: interrupted, stopping workers"
- Exit status: 130
- No stats_worker.py processes appeared in the subsequent process check

This verified cleanup for that Ctrl-C test. I did not separately
test SIGTERM or reproduce the original script's orphan-worker fault.

Ctrl-C sends SIGINT to the foreground process group. Background
workers can inherit an ignored SIGINT disposition, so explicitly
terminating and waiting for recorded worker PIDs provides cleanup.
If a parent exits while children remain alive, the children are
reparented, commonly to PID 1 inside this container.

## Worker experiment

### Hardware and environment

- MacBook Air (Mac14,2), Apple M2
- 8 physical cores: 4 performance and 4 efficiency
- 8 logical CPUs
- macOS 26.6.2
- CPUs available in the container: 4
- Container memory limit: 2147483648 bytes (2 GiB)
- Container swap limit: 0

### Method and results

I ran:
bash tools/sweep.sh saL1mZzz

The script measured 1, 2, 4, 8 and 16 workers three times each.
All 15 raw observations, including user and system CPU times,
are saved in members/saL1mZzz/sweep.csv.

| Workers | Run 1 elapsed (s) | Run 2 elapsed (s) | Run 3 elapsed (s) | Mean elapsed (s) |
|---|---:|---:|---:|---:|
| 1 | 33.70 | 38.28 | 45.86 | 39.28 |
| 2 | 17.85 | 48.94 | 23.40 | 30.06 |
| 4 | 9.83 | 25.59 | 21.16 | 18.86 |
| 8 | 14.37 | 22.54 | 24.79 | 20.57 |
| 16 | 18.40 | 22.12 | 26.28 | 22.27 |

### Interpretation

On my machine, mean elapsed time decreased from 1 to 4 workers,
then increased with 8 and 16. Four workers had the lowest mean,
approximately 2.08 times faster than one worker by mean elapsed time.

There was substantial variation between repetitions, especially at
two workers. I retained all observations. The measurements alone
do not identify whether background activity, thermal conditions,
power settings or another factor caused the variation.

The default of nproc selects four workers in my container.
This matches the best mean observed in this experiment. Although
the Mac has eight cores, this container exposes only four CPUs.
Additional workers compete for available CPU resources and can
add scheduling and other overhead rather than useful parallelism.

Team curves can differ because of CPU allocation, core performance,
physical versus logical CPU counts, memory and system conditions.
A measured comparison of each teammate's curve still requires
their sweep data and hardware details.

### Verification

After the sweep, tools/check.py returned PASS for every pipeline
output and every member folder. Git staging, commits and pushing
must still be checked separately.

## Full-pipeline verification

I started the pipeline from /home/analyst, outside the repository:

/usr/bin/time -f "$T" ./work/ospc-lab1-b1/run_report.sh

All five steps completed, including stats with 4 workers.
Exit status: 0.

- Elapsed: 50.37 s
- User CPU: 78.49 s
- System CPU: 4.44 s
- Peak memory: 1266136 KB

After this run, python3 tools/check.py returned PASS for every
pipeline output and every member folder.

This confirms successful execution from the home directory.
Git commits, pushing and the team chart require separate checks.
