# Lab 1: The Nightly Report

Write your answers in this file. Keep them short: a few sentences, the commands
you used, and the numbers you measured. Copy the lines of output that matter,
not whole screens.

## Warm-up: Generating the report

- What happened, and why:
- Your fix, and how it reached your teammates:

## Task 1: Generating the report… again

- Symptom:
- Commands and recordings you used, why you chose them, and what they showed:
- Cause:
- Fix:
- Before and after (your measurements):

## Task 2: Extracting data

- Symptom:
- Commands and recordings you used, why you chose them, and what they showed:
- Cause:
- Fix:
- Before and after (your measurements):

## Task 3: Auditing

- Symptom:
- Commands and recordings you used, why you chose them, and what they showed:
- Cause:
- Fix:
- Before and after (your measurements):

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

- Symptom:
- Commands and recordings you used, why you chose them, and what they showed:
- Cause:
- Fix:
- Before and after (your measurements):

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
