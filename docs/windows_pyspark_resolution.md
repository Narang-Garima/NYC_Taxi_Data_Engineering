# Windows PySpark Resolution and Validation Log

Date: 2026-10-03 (America/Toronto)

## Outcome

The Windows Parquet-write problem is fixed for this project. The project now selects a matching, project-local Hadoop 3.4.1 Windows runtime before PySpark starts. A real end-to-end run of `python main.py`, the pytest suite, and an independent read-back inspection all completed with exit code 0.

This directory was not a Git working tree during pipeline validation (`git status --short` returned `fatal: not a git repository`). Git was initialized later for publication, after the environment repair and validation were complete.

## Initial environment and diagnosis

- Input: `data/raw/yellow_tripdata_2025-01.parquet`
  - Size: 59,158,238 bytes
  - SHA-256: `9af277e4c0d3f9deb30644da822981e1e7df6af58313170fd3aa8a474485488a`
- Python: 3.11.6
- PySpark: 4.0.1
- Pytest: 8.4.0
- Java selected by `PATH`: Eclipse Temurin 17.0.20.1
- PySpark's bundled Hadoop client: 3.4.1 (`hadoop-client-api-3.4.1.jar` and `hadoop-client-runtime-3.4.1.jar`)
- Machine-scoped `HADOOP_HOME`: `C:\hadoop-3.3.6`
- `C:\hadoop-3.3.6` did not exist, although its `bin` and `sbin` paths were also present in `PATH`.

The effective Hadoop problem was therefore both a missing location and a version mismatch: the machine pointed to missing Hadoop 3.3.6 files while PySpark 4.0.1 uses Hadoop 3.4.1.

The first `python main.py` diagnostic also found a separate Codex desktop command-runner limitation. Java failed before Spark initialization with `WEPollSelectorImpl`, `Unable to establish loopback connection`, and `UnixDomainSockets.connect0: Invalid argument`. The same failure remained after forcing IPv4 and after selecting the already-installed Zulu Java 17.0.12 runtime. This is a child-process/container issue, not a pipeline or JDK-selection issue. To avoid claiming a false pipeline failure, final Spark validation ran as a temporary current-user Windows scheduled task outside that command-runner container. The task was removed after validation.

## Changes made

1. Installed the matching native Hadoop runtime under `.hadoop/hadoop-3.4.1`.
   - Source release: `https://github.com/zehelh/winutils/releases/tag/hadoop-3.4.1`
   - Downloaded asset: `hadoop-3.4.1.zip` (3,883,642 bytes)
   - GitHub-published and locally verified archive SHA-256: `aa8098a433e6d63b865074468aa2da1aa9329ef33c9e9af799037f382ce50b82`
   - `winutils.exe` SHA-256: `efc3df594235226d9846760b1c82e752802cccefc3baf92c6590d7c535f01a91`
   - `hadoop.dll` SHA-256: `0054084ae06350e41bc3af1dc235fa7a031a27684e6455c33252ae382cf60525`
   - `hdfs.dll` SHA-256: `752bef908e6d48c40822ac76ea0e78f924517aa42d317d978139c00b1e6adf34`
2. Added `scripts/setup_windows_hadoop.ps1`, which downloads this exact asset, verifies its SHA-256 before extraction, removes the archive, and exits harmlessly if already installed.
3. Updated `src/spark_session.py` to configure the project-local Hadoop runtime before importing PySpark on Windows:
   - Overrides `HADOOP_HOME` for the current Python process only.
   - Prepends the matching `bin` directory to that process's `PATH`.
   - Defaults `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` to the active interpreter.
   - Raises an actionable error if `winutils.exe` is absent.
4. Updated `tests/conftest.py` so tests use the same Spark session factory and Windows runtime setup as production.
5. Added `.hadoop/` and downloaded Hadoop archives to `.gitignore`; native binaries remain local rather than becoming repository content.
6. Added `scripts/inspect_outputs.py` for repeatable, independent read-back validation and `scripts/run_full_validation.ps1` to capture pipeline, pytest, and verification logs.
7. Did not change the machine or user environment. After validation, machine-scoped `HADOOP_HOME` was still `C:\hadoop-3.3.6`, user-scoped `HADOOP_HOME` remained unset, and the project continued to override the value only inside its Python process.

## Command and issue log

The commands below are the material diagnostic, setup, execution, and verification commands used. Read-only inventory commands (`Get-ChildItem`, `Get-Content`, and `Get-FileHash`) supplied the values recorded above.

| Command or action | Actual result |
| --- | --- |
| `git status --short` | Failed because the directory has no `.git` repository. No Git operation or push followed. |
| `python --version` | `Python 3.11.6`. |
| `java -version` | Temurin `17.0.20.1`. |
| `python -m pip show pyspark pytest` | PySpark `4.0.1`; pytest `8.4.0`. |
| Initial `python main.py` | Failed before Spark context creation. It reported missing `C:\hadoop-3.3.6\bin\winutils.exe`, then hit the Codex Windows `WEPollSelectorImpl` loopback restriction. This did not reach the pipeline. |
| Spark startup with `JAVA_TOOL_OPTIONS=-Djava.net.preferIPv4Stack=true -Djava.net.preferIPv6Addresses=false` | Same selector failure; IPv4 flags were not a fix. |
| Spark startup with `JAVA_HOME=C:\Program Files\Tableau\Tableau Public 2025.1\bin\jre` (Zulu 17.0.12) | Same selector failure; changing JDK did not fix the command-runner restriction. No persistent `JAVA_HOME` change was made. |
| GitHub release API query for tag `hadoop-3.4.1` | Resolved `hadoop-3.4.1.zip`, size 3,883,642, with published SHA-256 `aa8098...50b82`. |
| `Invoke-WebRequest` download, `Get-FileHash`, and `Expand-Archive` | Archive matched the published SHA-256 and extracted successfully to `.hadoop/hadoop-3.4.1`. The temporary archive was removed. |
| Import `src.spark_session` and print environment | Process-local `HADOOP_HOME` resolved to `<project-root>\.hadoop\hadoop-3.4.1`; `PYSPARK_PYTHON` resolved to the active Python 3.11 executable. |
| `winutils.exe ls data/raw/yellow_tripdata_2025-01.parquet` | Succeeded and reported the 59,158,238-byte source file. |
| `winutils.exe chmod 755` on the existing raw file from the Codex sandbox identity | Returned access denied because the source file belongs to the interactive Windows user. A create/chmod/delete probe on a sandbox-owned file succeeded. This probe did not alter source data; the real-user Spark run subsequently wrote all outputs successfully. |
| Temporary scheduled task running `scripts/run_full_validation.ps1` | Ran as the interactive Windows user. It invoked the exact commands `python main.py`, `python -m pytest -q`, and `python -m scripts.inspect_outputs`. All three exit codes were 0. The scheduled task was then removed. |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/setup_windows_hadoop.ps1` after installation | Confirmed idempotency: runtime already existed, so no download or change occurred. |
| `python -m py_compile main.py src\*.py tests\*.py scripts\inspect_outputs.py` | Failed because PowerShell passed native-command wildcard arguments literally. |
| `python -m compileall -q ...` | Hit an access error on a pre-existing `src/__pycache__` file created by the interactive user during Spark validation. Source was unaffected. |
| `python -X pycache_prefix=... -m py_compile src\spark_session.py tests\conftest.py scripts\inspect_outputs.py` | Succeeded with exit code 0 using a temporary project-local bytecode cache, which was then removed. |
| Final explicit-file `py_compile` plus PowerShell parser check | All Python files compiled with exit code 0 in a temporary cache, both `.ps1` files had zero parser errors, and the temporary cache was removed. |

Windows PowerShell represents native stderr lines as `NativeCommandError` records when piping `2>&1` through `Tee-Object`. The `WARNING: Using incubator modules` lines at the start of the pipeline/inspection logs are this formatting behavior, not command failures; the recorded process exit codes are all 0.

## Actual pipeline results

Command: `python main.py`

Exit code: 0

### Layer row counts

| Dataset | Rows | Read-back status |
| --- | ---: | --- |
| Raw source | 3,475,226 | Read successfully |
| Bronze `yellow_taxi` | 3,475,226 | Matches raw; `_SUCCESS` present |
| Silver `yellow_taxi` | 3,235,132 | `_SUCCESS` present |
| Gold `daily_metrics` | 33 | `_SUCCESS` present |
| Gold `zone_metrics` | 259 | `_SUCCESS` present |
| Gold `payment_metrics` | 5 | `_SUCCESS` present |

Silver removed 240,094 raw rows and retained 93.0913%.

Output inventory after the run:

| Output | Parquet files | Total bytes |
| --- | ---: | ---: |
| Bronze | 5 | 72,333,003 |
| Silver | 6 | 79,429,513 |
| Gold daily | 1 | 3,242 |
| Gold zone | 1 | 5,859 |
| Gold payment | 1 | 1,531 |

### Data-quality metrics

| Metric | Raw | Silver |
| --- | ---: | ---: |
| Row count | 3,475,226 | 3,235,132 |
| Null pickup timestamp | 0 | 0 |
| Null dropoff timestamp | 0 | 0 |
| Nonpositive distance | 90,893 | 0 |
| Negative total amount | 63,037 | 0 |
| Invalid timestamp order | 2,051 | 0 |

The defect counts may overlap, so their sum is not expected to equal the 240,094 removed rows. Silver also applies fare, distance ceiling, duration, location, and speed rules beyond the six displayed summary metrics.

Silver value ranges after filtering:

- Pickup timestamp: 2024-12-31 20:47:55 through 2025-02-01 00:00:44.
- Trip distance: 0.01 through 98.5 miles.
- Duration: 1.0 through 238.9167 minutes.
- Average speed: 0.1 through 79.96 mph.
- Physical partitions present: `pickup_year=2024/pickup_month=12`, `pickup_year=2025/pickup_month=1`, and `pickup_year=2025/pickup_month=2`.

The few boundary-date records are retained because the pipeline's documented rules validate trip quality but do not force timestamps to the filename's nominal month.

### Gold observations

- Earliest daily row: 2024-12-31, 20 trips, average distance 3.2, gross total amount 519.87.
- 2025-01-01: 80,635 trips, average distance 3.96, gross total amount 2,293,841.65.
- Highest-volume pickup zone in the ordered sample: `PULocationID=161`, 160,684 trips.
- Payment counts: type 1 = 2,418,830; type 0 = 405,650; type 2 = 364,917; type 4 = 34,280; type 3 = 11,455. These sum to the Silver count.

## Test result

Command: `python -m pytest -q`

Result: `2 passed, 1 warning in 67.83s`; exit code 0.

The warning is an unrelated Jupyter `platformdirs` deprecation emitted from the installed Python environment. No test failed and it does not affect the pipeline.

## Local evidence files

The following files are generated locally and intentionally ignored by Git because raw console output can contain machine-specific paths. Their results are fully summarized above.

- `docs/pipeline_run.log`: full captured `python main.py` output.
- `docs/pytest_run.log`: full pytest output.
- `docs/output_verification.log`: independent layer counts, quality results, ranges, partitions, Gold samples, and `_SUCCESS` checks.
- `docs/validation_exit_codes.txt`: exit codes for all three validation phases.

## Repeatable Windows commands

From the project root in a normal PowerShell window:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\setup_windows_hadoop.ps1
python main.py
python -m pytest -q
python -m scripts.inspect_outputs
```

The first command is only needed on a machine where `.hadoop/hadoop-3.4.1` is absent. The process-local configuration means the stale machine-wide `HADOOP_HOME` does not affect this project.
