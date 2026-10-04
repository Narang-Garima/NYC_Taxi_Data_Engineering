import os
import sys
from pathlib import Path


def _configure_windows_runtime() -> None:
    """Use the project-local Hadoop native binaries required by Spark on Windows."""
    if os.name != "nt":
        return

    hadoop_home = Path(__file__).resolve().parents[1] / ".hadoop" / "hadoop-3.4.1"
    winutils = hadoop_home / "bin" / "winutils.exe"
    if not winutils.is_file():
        raise RuntimeError(
            f"Missing {winutils}. Run scripts/setup_windows_hadoop.ps1 first."
        )

    os.environ["HADOOP_HOME"] = str(hadoop_home)
    hadoop_bin = str(hadoop_home / "bin")
    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    if hadoop_bin.casefold() not in {entry.casefold() for entry in path_entries}:
        os.environ["PATH"] = hadoop_bin + os.pathsep + os.environ.get("PATH", "")
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)


_configure_windows_runtime()

from pyspark.sql import SparkSession

def get_spark(app_name: str = "NYC-Taxi-Data-Engineering") -> SparkSession:
    return (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.sql.session.timeZone", "America/New_York")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )
