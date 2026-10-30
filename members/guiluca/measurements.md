## Section 5.1 — Warm-up: Generating the Report

**Initial command:** `./run_report.sh`
The command seemmed to have ran but there was a kill message that appeared, no problem with permissions ecause my laptop is windows.

**Comparison with teammates:** Some of my teammates had mac and therefore had to either use chmd to add executing permissionsto the program or run it with bash which basically bypasses the need for permission of the OS.

## Section 5.2 — Task 1: Generating the Report Again

1. Exit status 137 means the program was killed by SIGKILL (signal 9). The OOM killer is responsible, as indicated by memory.events.

2. The table size is not the total memory consumption. Python also uses memory for intermediate calculations, data structures, and runtime overhead, so thought the table measured (887MiB) that is not the total size of the process to create the table is probably larger, causing the OOM killer to act.

3.

| Orders    | Table size (MiB) | Elapsed (s) | User (s) | System (s) | Peak memory (KB) |
| --------- | ---------------: | ----------: | -------: | ---------: | ---------------: |
| 1,000,000 |              106 |        2.82 |     2.59 |       0.68 |           504572 |
| 2,000,000 |              211 |        3.53 |     3.78 |       0.70 |           854724 |
| 4,000,000 |              423 |        6.51 |     6.03 |       1.41 |          1567968 |

Peak memory increases approximately linearly with the number of orders. Based on the measurements, processing 8.4 million orders would require approximately 3 GB of peak memory, exceeding the container's approximately 2 GB limit.

4. Python buffers its output but since the process is killed before flushing the buffer, the loaded message does not go through as the stdin of the next command and therefore does appear in report.log.

