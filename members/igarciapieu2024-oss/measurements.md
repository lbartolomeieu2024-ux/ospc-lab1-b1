# Task Warmup
- Questions
1) ./file needs x. On MacOS (-rw-r--r-- ) users in neither of the triplets have permission of x (execute in a file).  They can fix it with chmod u+x , although it can only be done by the owner.
2) bash run_report.sh works, because bash is a program that reads the commands you type and runs them, which requires r permission. Therefore MacOS users have r permission, so they can do it.
3) On a Mac, it stores r/w/x Linux permission for every file. When they cloned the repo, git created run_report.sh with the permissions saved in the repo. On Windows it does not store r/w/x permissions, it has its own permission system. The repo folder is a Windows folder and Windows has no r/w/x permissions, so when the container looks at the folder, every file is shown as rwxrwxrwx. That is why in my Windows computer both commands worked.

- Results in my terminal:
```
analyst@ospc:~/work/ospc-lab1-b1$ ./run_report.sh
	Nightly report started: 07:36:13
	extracts: done
	report: loaded 8,400,000 orders (887 MiB)
	./run_report.sh: line 10:    33 Killed                     python3 steps/report.py
	audit: 8,400,000 lines written
	segments: done
	stats: input ready
	stats: done with 16 workers
	Nightly report finished: 07:40:49
analyst@ospc:~/work/ospc-lab1-b1$ bash run_report.sh
	Nightly report started: 07:44:55
	extracts: done
	report: loaded 8,400,000 orders (887 MiB)
	run_report.sh: line 10:   223 Killed                     python3 steps/report.py
	audit: 8,400,000 lines written
	segments: done
	stats: input ready
	stats: done with 16 workers
	Nightly report finished: 07:49:28
```
# Task 1: Generating the Report. 
- Questions
1) Exit status 137 means that the program was stopped by a SIGKILL 9  (137-128), not by the program itself. SIGKILL cannot be caught, so report.py could not print an error or write its output file. The signal was sent by the kernel out of memory killer because the cgroup reached its memory limit. The line omm_kill in memory.events confirms it. The line max 485 shows the group reached its limit 485 times before the kill. 
2) Because the printed table 2GB counts only for the final table, while the peak memory counts for everything the process is holding at the same time. 
3) Table with number orders, size of the table and the peak memory, and how much memory the whole file would need 
The Peak Memory grows linearly, in 1 million = 106Mib the Peak is 504856Mib, 2 million 211MiBm the Peak is 856508, which makes a difference of 351,652. For 4 million= 423MiB, which has a peak of 1568312, which makes a difference of 711804, divided by 2 is 355902. So we can estimate that the peak memory grows around 350,000 KB each 1 million orders more, so Peak in 8.4Million to be 1568,312 (peak in 4 million orders) + 4.4 * 355,902 = 3,134,000 KB approx. 

| Orders | Table size | Peak memory |
|---:|---:|---:|
| 1,000,000 | 106 MiB | 504,856 KB |
| 2,000,000 | 211 MiB | 856,508 KB |
| 4,000,000 | 423 MiB | 1,568,312 KB |
| 8,400,000 | 887 MiB | 3,134,000 KB |

4) Because report.py’s output does not go to the terminal: it goes through a pipe as the input of tee. When output goes to a pipe, Python buffers it and only writes it out when the buffer is full or the program ends normally. (On a terminal, it writes each line immediately.) The short loaded line was still waiting in report.py’s buffer when the OOM killer sent SIGKILL. SIGKILL cannot be caught, so the program had no chance to write out its buffer. The line never reached the tee, so it is missing from both the screen and the log. 

- Results in my terminal:
```
python3 steps/report.py
echo $?
	report: loaded 8,400,000 orders (887 MiB)
	python3 steps/report.py
	Killed                     python3 steps/report.py
	137

cat /sys/fs/cgroup/memory.events
	low 0
	high 0
	max 6583
	oom 5
	oom_kill 5 #because it takes into account the counter until the container stops
	oom_group_kill 0

head -n 1000001 ~/data/sales_2025.csv > /tmp/orders_1m.csv
DATA=/tmp/orders_1m.csv OUT=/tmp /usr/bin/time -f "$T" python3 steps/report.py
	report: loaded 1,000,000 orders (106 MiB)
	report: done

head -n 2000001 ~/data/sales_2025.csv > /tmp/orders_1m.csv
DATA=/tmp/orders_1m.csv OUT=/tmp /usr/bin/time -f "$T" python3 steps/report.py
	report: loaded 2,000,000 orders (211 MiB)
	report: done

head -n 4000001 ~/data/sales_2025.csv > /tmp/orders_1m.csv
DATA=/tmp/orders_1m.csv OUT=/tmp /usr/bin/time -f "$T" python3 steps/report.py
	report: loaded 4,000,000 orders (423 MiB)
	report: done

python3 steps/report.py | tee /tmp/report.log
cat /tmp/report.log #nothing because of what explained in Step 4
```
# Task 2: Extracting Data. 
- Questions
1) The file is empty because grep has been reading a non-existing directory that was previously changed by cd. When doing ../data/sales_2025.csv. 
Defines OUT as home/analyst/data/out and creates and changes to directory home/analyst/data/out/extracts. 
When doing ../data/sales_2025.csv, as it is a relative path it starts from the current running directory and goes to home/analyst/data/out/data/sales_2025.csv, which does not exist (as the real file is /home/anayst/data/sales_2025.csv)

2) Because a pipeline status is the status of the last command. In grep the last command is cut which works well. If we did PIPESTATUS it would give as 2 0. It prints done because bash does not stop after a failed command unless told to (set -e or checking $?), so the script continues to echo "extracts: done", which prints the text without checking anything. Since echo is the last command and succeeds, the script exits with status 0.

3) It hides the error message grep would have returned as there was not an existing file, as grep stderr with 2>/dev/null is sended yo /dev/null where it is discarded. The exact message is “grep: ../data/sales_2025.csv: No such file or directory”. Errors that took place in the other part of the pipeline (cut) would still appear or from mkdir, cd, or >region.csv. Also the grep output is still going to go to cut. 

4) -e → stop at the first error, so without -e if a command fails, bash ignores it and continues. Work together with pipefail
-u → a variable that does not exist gives an error. Example without -u using a variable that has never been given a value gives empty text with no error. 
Pipefail → a pipeline fails if any of the parts fail. Does not stop the command from running, only changes the pipeline status. 

With set -euo pipefail at the top of extracts.sh. 
grep fails with status 2 because pipefail makes the pipeline’s status 2 instead of cut’s 0. Important that the cut still runs, only the reported status changes.
-e then sees a failure and stops the script immediately, so echo "extracts: done" is never reached and the script exits with a non-zero status. -e alone would not be enough, because without pipefail the pipeline’s status is 0. 
-u changes nothing here, because $region and $OUT are always set. 
-o because a name pipefail goes later

Therefore to make extracts.sh stop with an error I would have used set -eo pipefail

- Results in the terminal
```
bash steps/extracts.sh
echo $?
ls -l ~/data/out/extracts
	extracts: done
	0
	total 0
	-rw-r--r-- 1 analyst analyst 0 Oct 31 09:01 Benelux.csv
	-rw-r--r-- 1 analyst analyst 0 Oct 31 09:01 DACH.csv
	-rw-r--r-- 1 analyst analyst 0 Oct 31 09:01 France.csv
	-rw-r--r-- 1 analyst analyst 0 Oct 31 09:01 Iberia.csv
	-rw-r--r-- 1 analyst analyst 0 Oct 31 09:01 Italy.csv
	-rw-r--r-- 1 analyst analyst 0 Oct 31 09:01 Nordics.csv

less steps/extracts.sh
	#!/bin/bash
	# One file per region for the regional managers, with the columns
	# order_id, order_date, product_category, quantity, unit_price.	
	OUT=${OUT:-$HOME/data/out}
	mkdir -p "$OUT/extracts"
	cd "$OUT/extracts"
	for region in Iberia DACH France Italy Benelux Nordics; do
	    grep ",$region," ../data/sales_2025.csv 2>/dev/null | cut -d, -f1,2,4,6,7 > "$region.csv"
	done
	echo "extracts: done"
	
cd ~/data/out/extracts
grep ",Iberia," ../data/sales_2025.csv | cut -d, -f1,2,4,6,7 | wc -l
echo ${PIPESTATUS[@]}
pwd
cd -
	grep: ../data/sales_2025.csv: No such file or directory
	0
	2 0 0
	/home/analyst/data/out/extracts
	/home/analyst/work/ospc-lab1-b1
```
# Task 3: Auditing. 

- Questions
1) For 100,000 orders, audit.py made about 100689 openat, 100001 write and 100677 close calls, which is roughly 100,000 of each, plus a few hundred extra openat/close from Python starting up. It’s so many because for every order it opens the file, writes one line and closes it: 3 system calls per order, about 300,000 in total. Each one is a request to the kernel, which is why system time is high. 

2) In the run of the whole file, the time went to the user by 139,06 seconds and 60.48 seconds to the system. What it went to the kernel was (60.48/139,06+60,48) = 30.3%
In report.py the time to use was 23.06 u , the time to the system was 7.31s so the time that went to the kernel was 24%, this would mean that it executed fewer system calls. The kernel time in report.py is lower because it comes only from reading the file (system call read) and getting it from memory (system call mmap/brk). 

3) No. close() only moves the data from Python’s buffer (in the process) to the OS page cache (in the kernel’s RAM). It does not wait for the data to be copied to the disk. The kernel writes it to disk later and only os.fsync() forces it. So after close(), a line can still be lost if the power fails before the kernel writes it back.
What close() does guarantee is that the line survives if the process is killed (kill -9), because the data has left the process. 

4) With a single open file, Python collects the lines in its buffer and makes one write system call only when the buffer is full (and one last write for what remains when the file is closed). So the number of write calls is about file size ÷ buffer size, rounded up.
The buffer is 128 KiB = 128 × 1,024 = 131,072 bytes. Each line is about 21.5 bytes (180,634,390 bytes ÷ 8,400,000 lines), so the 100,000-order sample file is about 2,150,000 bytes: 2,150,000 ÷ 131,072 = approx 16.4 → about 17 write calls, instead of ~100,000.

- Results in the terminal
```
export DATA=~/data/sales_2025_sample.csv
/usr/bin/time -f "$T" python3 steps/audit.py
unset DATA
/usr/bin/time -f "$T" python3 steps/audit.py
	audit: 100,000 lines written
	audit: 8,400,000 lines written

export DATA=~/data/sales_2025_sample.csv
strace -c -e trace=openat,write,close python3 steps/audit.py
ls -l ~/data/out/audit_2025.csv
unset DATA
```
# Task 4: Segmenting. 
When we run first segment we can see that the elapsed time is large, and the user time is much longer than the system time, meaning that is using CPU time inside the code program not in the kernel. Therefore to locate the function that is being called the most in Python we use cProfile, not longer strace, that measures the number of functions in Python. By doing it we can see that there were for 100,000 orders 3,646,598 function calls. By identifying visualizing the code we could see that in the function segments at very order it convert the text into date with srptime (row by row in the loop, as segment function is inside the for loop) instead of converting the whole column at once. Wiithout the fix and using pandas per order it repeats 10 Python functions for the setup, while pandas does everything in a single call. 

But we must be aware that there is a tradeoff as the peak memory grows because now the whole column is converted at once.
- Results in the terminal
```
#The results were after the fix but in the Report you can see what was previosuly. 
T='%e s elapsed, %U s user, %S s system, %M KB peak memory'
/usr/bin/time -f "$T" python3 steps/segments.py
	segments: done
	24.49 s elapsed, 23.08 s user, 1.51 s system, 1177272 KB peak memory

DATA=~/data/sales_2025_sample.csv python3 -m cProfile -s tottime steps/segments.py > /tmp/profile.txt
head -n 25 /tmp/profile.txt #As it is after the fix the number of function calls and time has decreased although the peak memory increased. Also stripr does not longer appear
		1152310 function calls (1139930 primitive calls) in 1.629 seconds
	   Ordered by: internal time
	   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
	     2180    0.428    0.000    0.428    0.000 {built-in method posix.stat}
	   200514    0.185    0.000    0.185    0.000 array.py:818(__iter__)
	        1    0.122    0.122    1.629    1.629 segments.py:1(<module>)
	      442    0.089    0.000    0.089    0.000 {built-in method marshal.loads}
	        1    0.083    0.083    0.088    0.088 c_parser_wrapper.py:203(read)
	   100000    0.050    0.000    0.050    0.000 segments.py:16(segment)
	   100138    0.049    0.000    0.070    0.000 __init__.py:453(_make)
	   108779    0.033    0.000    0.033    0.000 {method 'get' of 'dict' objects}
	    68/37    0.033    0.000    0.299    0.008 {built-in method _imp.exec_dynamic}
	       68    0.029    0.000    0.029    0.000 {built-in method _imp.create_dynamic}
	        7    0.025    0.004    0.032    0.005 string_arrow.py:195(_from_sequence)
	      448    0.018    0.000    0.018    0.000 {method 'read' of '_io.BufferedReader' objects}
	104488/104295    0.017    0.000    0.021    0.000 {built-in method __new__ of type object at 0xa99760}
	      887    0.017    0.000    0.018    0.000 <frozen importlib._bootstrap_external>:137(_path_split)
	      444    0.016    0.000    0.016    0.000 {built-in method _io.open_code}
	       68    0.016    0.000    0.016    0.000 {built-in method posix.listdir}
	139656/138967    0.013    0.000    0.013    0.000 {built-in method builtins.len}
	  932/921    0.013    0.000    0.093    0.000 {built-in method builtins.__build_class__}
	      442    0.012    0.000    0.101    0.000 <frozen importlib._bootstrap_external>:509(_compile_bytecode)
cat steps/segments.py
		"""Number of orders per region, quarter and order size (segments.csv)."""
	
	import os
	from datetime import datetime
	
	import pandas as pd
	
	DATA = os.environ.get("DATA", os.path.expanduser("~/data/sales_2025.csv"))
	OUT = os.environ.get("OUT", os.path.expanduser("~/data/out"))
	os.makedirs(OUT, exist_ok=True)
	
	orders = pd.read_csv(DATA, usecols=["order_date", "region", "quantity", "unit_price"])
	orders["quarter"] = pd.to_datetime(orders["order_date"], format="%Y-%m-%d").dt.quarter #code corrected now it converts the whole column at once with the tradeoff of peak memory
	
	
	def segment(order):
	    quarter = order.quarter #code corrected, does not longer do this in the loop 
	    value = order.quantity * order.unit_price
	    if value >= 500:
	        size = "large"
	    elif value >= 100:
	        size = "medium"
	    else:
	        size = "small"
	    return f"Q{quarter} {size}"

	
	counts = {}
	for order in orders.itertuples(index=False):
	    key = (order.region, segment(order))
	    counts[key] = counts.get(key, 0) + 1
	
	table = pd.Series(counts).rename_axis(["region", "segment"]).unstack(fill_value=0)
	table.to_csv(os.path.join(OUT, "segments.csv"))
	print("segments: done")
```
	
