# Lab 1: The Nightly Report

Write your answers in this file. Keep them short: a few sentences, the commands
you used, and the numbers you measured. Copy the lines of output that matter,
not whole screens.

## Warm-up: Generating the report

- Team comparison (saL1mZzz): On my laptop, ./run_report.sh worked immediately. ls -l run_report.sh showed -rwxr-xr-x, meaning execute permission was already enabled for the owner, group and others. On Pablo's laptop, the permissions were -rw-r--r--, so running the script directly returned "Permission denied". The difference was the missing execute (x) permission on his copy. He fixed it using chmod +x run_report.sh. The executable-bit change was subsequently committed and shared through Git.

## Task 1: Generating the report… again

- Symptom: `./run_report.sh` printed `Nightly report finished` with exit status 0, although `report.py` had been killed (`Killed`, status 137). The steps after it ran anyway.
- Commands and what they showed: before the fix, the full run went from `Nightly report started` to `Nightly report finished`, with `Killed python3 steps/report.py` in the middle. After the fix, `/usr/bin/time -f "$T" ./run_report.sh; echo $?` stops right after `Killed`: `Command exited with non-zero status 137`, `19.49 s elapsed, 18.90 s user, 3.98 s system, 2089304 KB peak memory`, and `137`. No `audit:`, `segments:` or `stats:` lines appear.
- Cause: the script did not check the exit status of any step. Without `set -e`, bash runs the next command even when one fails, so the final `echo` always succeeded.
- Fix: added `set -euo pipefail` after the shebang. `-e` stops at the first failing command, `-u` stops on unset variables, and `pipefail` makes a pipeline fail if any of its commands fails. Commit `05dd067`, pushed as `fffb6f0`.
- Before and after: the script printed `finished` after `report.py` was killed; after the fix it stops at that step with status 137.

## Task 2: Extracting data

- Symptom: `bash steps/extracts.sh` printed `extracts: done` and exited with 0 in 0.05 s, but all six files in `~/data/out/extracts` were 0 bytes.
- Commands and recordings you used, why you chose them, and what they showed: `less steps/extracts.sh` to read what the script does. Then I ran its pipeline by hand, from the folder it works in and without `2>/dev/null`: `cd ~/data/out/extracts; grep ",Iberia," ../data/sales_2025.csv | cut -d, -f1,2,4,6,7 | wc -l` printed `grep: ../data/sales_2025.csv: No such file or directory` and `0`. `echo ${PIPESTATUS[@]}` printed `2 0 0`, and `pwd` showed `/home/analyst/data/out/extracts`. No recordings: the error message and the exit statuses were enough.
- Cause: the script does `cd "$OUT/extracts"` and then reads `../data/sales_2025.csv`. From that folder this means `/home/analyst/data/out/data/sales_2025.csv`, which does not exist (the script also ignores `DATA`). `grep` fails with status 2, but `2>/dev/null` hides its message, the status of the pipeline is the status of its last command (`cut`, 0), and the script never checks statuses, so it ends with `echo "extracts: done"` and exit status 0. The files exist but are empty because the shell creates each `$region.csv` for the redirection before running the commands.
- Fix: added `set -euo pipefail`, read the input from `"$DATA"` (default `$HOME/data/sales_2025.csv`, like the other steps), removed `2>/dev/null`, and removed the `cd`, writing to `$OUT/extracts/$region.csv`, so the step works from any folder. With `pipefail`, `grep` would also stop the script if a region had no orders (status 1), but every region has orders.
- Before and after (your measurements):

| | Before | After |
|---|---|---|
| Full: elapsed / user / system | 0.05 / 0.01 / 0.04 s | 4.08 / 4.95 / 1.10 s |
| Full: peak memory | 6,564 KB | 8,576 KB |
| Rows in the six files | 0 | 8,400,000 |
| Input missing (`DATA=/tmp/nope.csv`) | `extracts: done`, exit 0 | grep error, exit 2, no `done` |
| Started from `~` | — | `extracts: done`, exit 0 |
| `check.py` extracts | 6 × FAIL | 6 × PASS |

The step now takes 4 s because it actually reads the 8.4 million orders. User time is higher than elapsed because `grep` and `cut` run at the same time, on two cores.

## Task 3: Auditing

- **Symptom:** The audit step took 237.51 seconds to process 8.4 million orders because, for every row, the output file was opened, written to, and closed, creating significant overhead.

- **Commands and recordings used, why we chose them, and what they showed:**
  - `/usr/bin/time -f "$T" python3 steps/audit.py` — Measured execution time, CPU time (user and system), and peak memory. It showed that almost half (49.3%) of CPU time was spent in the kernel.
  - `DATA=~/data/sales_2025_sample.csv strace -c -e trace=openat,write,close python3 steps/audit.py` — Counted file-related system calls on 100,000 orders. Before the fix, there were 100,691 `openat`, 100,001 `write`, and 100,677 `close` calls, confirming excessive file operations.
  - `python3 tools/check.py` — Verified that the optimized script produced the correct output, returning `PASS audit_2025.csv` with 8.4 million lines.
  - No process recordings were made; we used timing measurements and `strace`.

- **Cause:** The `with open(path, "a")` statement was inside the loop, causing the file to be opened and closed for every order. This prevented effective buffering because Python flushed its buffer every time the file was closed, generating unnecessary system calls.

- **Fix:** Moved `with open(path, "w") as f:` outside the loop, opening the file only once and keeping it open while writing all orders. This allows Python to buffer multiple lines before making write system calls.

- **Before and after (our measurements):**

  | Metric | Before | After |
  |---|---:|---:|
  | Elapsed time (8.4M orders) | 237.51 s | 14.14 s |
  | User CPU time | 119.24 s | 13.56 s |
  | System CPU time | 116.15 s | 1.52 s |
  | Peak memory | 633,932 KB | 633,680 KB |
  | `openat` calls (100K orders) | 100,691 | 692 |
  | `write` calls (100K orders) | 100,001 | 17 |
  | `close` calls (100K orders) | 100,677 | 678 |

  **Result:** The optimized script was approximately **16.8 times faster**, reducing elapsed time by 94%. The number of traced system calls decreased by 99.54%, while memory usage remained almost unchanged. The final output passed the correctness check.

## Task 4: Segmenting the orders

- Symptom:  segments.py takes 118.86 s on the full file (8.4M orders), much longer than reading the file does: report.py read the same 8.4M orders with only 23.06 s of user time. 
- Commands and recordings you used, why you chose them, and what they showed:
  - `/usr/bin/time -f "$T" python3 steps/segments.py`: to see how long each step takes and if the time went into the program own code (user time) or into the kernel (system). It showed on the full file, 118.86s of elapsed of of which 116.12 s user and 2.68 s system. 
  - `python3 -m cProfile -s tottime steps/segments.py`: because the user time was high, so we needed to see which Python function the time goes into, as the profiler counts every function call and the time. It showed `segment` (segments.py:15) is called 100,000 times, once per order, cumtime 1.272 s. Inside it, `strptime` (100,000 calls) takes 1.197 s.
  - `cat steps/segments.py`: to find the line that calls `strptime` once per order. It showed that `segment` converts each order's date inside the loop over all orders.
  - `python3 tools/check.py`: to check that the fix does not change the ouput. 
- Cause: segments.py spends 116,12s in user and 2.68s in the system, so it is spending the time using the CPU not executing system calls to the kernel. That is why as the problem is not system calls, we need to use profiler to detect every function call of the program and the time spent on it. After running the profiler we can see that with 100,000 orders the program made 3,646,598 function calls in 2.644. The function segment (segments.py:15) is called 100,000 times (once per order), cumtime 1.272 s. Inside it, strptime (100,000 calls) takes 1.197 s: it converts each order’s date from text, repeating the locale checks and text matching every time. As conclusion of second cause analysis each order date is being converted one at a time with strptime, instead of doing the whole column at once. In fact inside the code we can see that the function segment is called per order. 
- Fix: The code was slow because it converted each order date one by one inside the loop. The fix is to convert all the dates at once before the loop, with one pandas line that saves the quarter of every order in a new column. Then, inside the loop, the code reads that quarter instead of converting the date again. However we can see that memory grows (peak memory) as the whole date column is converted at once.
  - added after `read_csv`: `orders["quarter"] = pd.to_datetime(orders["order_date"], format="%Y-%m-%d").dt.quarter`
  - replaced the `strptime` line in `segment` with: `quarter = order.quarter`
- Before and after (your measurements):

| | Before | After |
|---|---|---|
| Sample: elapsed / user / system | 4.75 / 2.86 / 0.97 s | 2.09 / 1.64 / 0.34 s |
| Full: elapsed / user / system | 118.86 / 116.12 / 2.68 s | 39.63 / 37.26 / 2.39 s |
| Full: peak memory | 727,608 KB | 1,245,092 KB |
| Profile (sample): total calls | 3,646,598 | 1,152,310 |
| Profile (sample): strptime | 100,000 calls, 1.197 s | 0 |
| check.py segments.csv | — | PASS |

The step is faster (78.9 s less user time). But peak memory grows because the whole date column is converted at once, plus temporary arrays, but it stays below the 2 GiB limit. The fix trades memory for time. 

## Task 5: Computing the statistics

- Symptom: More workers did not make stats.sh faster, and after Ctrl-C the workers kept running. On my laptop (8 CPUs in the container) the default of 16 workers was slower than 8 workers, and after Ctrl-C ps -ef still listed python3 steps/stats_worker.py processes.
- Commands and recordings you used, why you chose them, and what they showed: (1) bash tools/sweep.sh mario-sanchez-garcia, to time the step with 1, 2, 4, 8 and 16 workers, three runs each. The mean elapsed time fell from about 51 s (1 worker) to 26 s (2), 13.6 s (4) and 9.0 s (8), and then rose to about 10.1 s with 16 workers; user and system CPU time also grew. (2) timeout --foreground -s INT 3 bash steps/stats.sh followed by ps -ef | grep stats_worker | grep -v grep: timeout sends SIGINT after 3 s, like Ctrl-C, so the test does not depend on my timing. It showed many stats_worker processes still alive with PPID 1.
- Cause: WORKERS defaulted to a fixed 16, whatever the laptop. With more workers than CPUs (8) the processes compete for the CPUs and the kernel switches between them: system time rose from 3.4 s to 4.2 s and user time from 61 s to 71 s, so 16 workers were slower than 8. The workers are started with & and the script neither kept their PIDs nor handled signals: Ctrl-C (SIGINT) ended the script, but the background workers kept running and were adopted by the process with PID 1.
- Fix: Two commits. (1) WORKERS=${WORKERS:-$(nproc)}: one worker per CPU that the container sees. (2) The script stores the PID of every worker (pids+=($!)) and has a trap on INT and TERM that runs kill "${pids[@]}", waits for them and exits with status 130, so Ctrl-C leaves nothing running.
- Before and after (your measurements): mean of 3 runs on my laptop.

| | Before (16 workers) | After (8 workers = nproc) |
|---|---|---|
| Elapsed | 10.06 s | 9.03 s |
| User | 70.6 s | 61.1 s |
| System | 4.16 s | 3.38 s |
| stats_worker alive after Ctrl-C | yes, PPID 1 | none |
| check.py stats.csv | - | PASS (72 region-months) |


## The worker experiment

Every member runs `tools/sweep.sh` on their own laptop. Then run
`python3 tools/plot_sweep.py` and commit `results/sweep.png`.

![Elapsed time against the number of workers](results/sweep.png)

- How does the elapsed time change with the number of workers on each laptop?
- Why do the curves of your laptops differ? Use the cores and threads of each
  laptop, listed in `TEAM.md`.
- Which default number of workers did you choose for `stats.sh`, and why?

## Use of generative AI
Follow the format in the syllabus: quote any generated text and name the tool
and the prompts; add the same note as a comment before any generated code. If
you did not use GenAI, write: "No content generated by AI technologies has been
used in this assignment."

Pablo Esteves (pestevesieu2024-jpg): I relied on Anthropic’s Claude to help walk me through the environment setup, the class exercises, and debugging steps/extracts.sh. Typical queries I used were practical questions like "lets do my part: extracts" and troubleshooting errors such as "why do i get access denied". Claude produced the updated code for steps/extracts.sh (which I explicitly flagged via an in-file comment). For Task 2, I provided Claude with my raw data/measurements to generate the initial draft, which I then thoroughly reviewed and edited myself.

Mario Sanchez Garcia (mario-sanchez-garcia): I used Anthropic's Claude (Claude desktop app) as a step-by-step tutor for the whole lab. I uploaded lab1_handout.pdf and screenshots of my terminal, and asked it to guide me through the lab one small step at a time. Claude proposed the commands and explained the outputs (permissions, exit status 137 and the OOM killer, memory.events, PIPESTATUS, strace counts, ps -ef and PPID). I ran every command myself on my laptop and checked the results. Generated code: the two changes to steps/stats.sh (default WORKERS=$(nproc), and storing the worker PIDs plus a trap on INT and TERM). The same note is a comment before those lines in the file. I tested them with timeout -s INT 3 bash steps/stats.sh followed by ps -ef, and with tools/check.py. Generated text: Claude drafted the Warm-up and Task 5 sections of this report from my own measurements; I read them and checked the numbers against my measurements.

Salim Cherraj (saL1mZzz): I used OpenAI's ChatGPT (GPT-6) as a step-by-step tutor to understand the lab instructions, troubleshoot terminal errors, and interpret my results. I uploaded the lab handout and screenshots of my terminal outputs. ChatGPT helped explain file permissions, Git commands, exit status 137, the OOM killer, memory usage, and output buffering with tee. 

Guilherme Oliveira (guiluca): I used chatgpt 5.6 sol to understand the instructions of the lab, troubleshoot any problems and errors that I had and guide me with the necessary commits and requirements of the lab activity. I was responsible for fixing the "audit.py" code and I used chatgpt to first understand the code line by line, which allowed me to spot the problem/inefficiency and fix it myself)

Irene García (igarciapieu2024-oss): I used Claude Anthropic, model Claude Opus 5.5 as a study tutor for this lab. I used it to guide me in the setup of the lab, explain the concepts behind each fault, to check if the interpretation of the outputs of my own measurements were correct, to explain line by line the coding, and correct the code I suggested to fix, and to review the wording of this report, to correct grammar mistakes. 

Luc? Bartolom?G?ez (lbartolomeieu2024-ux): I used Claude (Anthropic, claude.ai) to explain exit statuses, signals and `strace` output. For the `run_report.sh` fix I asked "how do I make a bash script stop when a step fails", and Claude suggested the line `set -euo pipefail`, which I added after the shebang and marked with a comment in the file.

