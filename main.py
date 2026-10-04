import argparse
from src.config import DATA_DIR, DEFAULT_INPUT
from src.spark_session import get_spark
from src.pipeline import run_pipeline

def parse_args():
    parser = argparse.ArgumentParser(description="NYC Yellow Taxi PySpark data pipeline")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Input Parquet file or glob")
    parser.add_argument("--data-dir", default=str(DATA_DIR), help="Output data directory")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    spark = get_spark()
    try:
        result = run_pipeline(spark, args.input, args.data_dir)
        print("\nRAW DATA QUALITY")
        result["before"].show(truncate=False)
        print("\nCURATED DATA QUALITY")
        result["after"].show(truncate=False)
        print("\nDAILY GOLD SAMPLE")
        result["daily"].show(10, truncate=False)
    finally:
        spark.stop()
