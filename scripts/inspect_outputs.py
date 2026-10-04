from pathlib import Path

from pyspark.sql import functions as F

from src.config import BRONZE_DIR, DEFAULT_INPUT, GOLD_DIR, SILVER_DIR
from src.quality import quality_summary
from src.spark_session import get_spark


def print_metrics(label, dataframe) -> None:
    metrics = quality_summary(dataframe).first().asDict()
    print(f"{label}_quality={metrics}")


def main() -> None:
    spark = get_spark("NYC-Taxi-Output-Verification")
    try:
        datasets = {
            "raw": spark.read.parquet(str(DEFAULT_INPUT)),
            "bronze": spark.read.parquet(str(BRONZE_DIR / "yellow_taxi")),
            "silver": spark.read.parquet(str(SILVER_DIR / "yellow_taxi")),
            "daily_gold": spark.read.parquet(str(GOLD_DIR / "daily_metrics")),
            "zone_gold": spark.read.parquet(str(GOLD_DIR / "zone_metrics")),
            "payment_gold": spark.read.parquet(str(GOLD_DIR / "payment_metrics")),
        }

        counts = {name: dataframe.count() for name, dataframe in datasets.items()}
        print(f"row_counts={counts}")
        print(f"rows_removed_raw_to_silver={counts['raw'] - counts['silver']}")
        print(f"silver_retention_pct={counts['silver'] / counts['raw'] * 100:.4f}")
        print_metrics("raw", datasets["raw"])
        print_metrics("silver", datasets["silver"])

        silver_stats = datasets["silver"].agg(
            F.min("tpep_pickup_datetime").alias("min_pickup"),
            F.max("tpep_pickup_datetime").alias("max_pickup"),
            F.min("trip_distance").alias("min_distance"),
            F.max("trip_distance").alias("max_distance"),
            F.min("trip_duration_minutes").alias("min_duration_minutes"),
            F.max("trip_duration_minutes").alias("max_duration_minutes"),
            F.min("average_speed_mph").alias("min_speed_mph"),
            F.max("average_speed_mph").alias("max_speed_mph"),
        ).first().asDict()
        print(f"silver_ranges={silver_stats}")

        partitions = sorted(
            str(path.relative_to(SILVER_DIR / "yellow_taxi"))
            for path in (SILVER_DIR / "yellow_taxi").glob("pickup_year=*/pickup_month=*")
            if path.is_dir()
        )
        print(f"silver_partitions={partitions}")

        for name in ("daily_gold", "zone_gold", "payment_gold"):
            print(f"{name}_sample")
            datasets[name].show(10, truncate=False)

        expected_paths = [
            BRONZE_DIR / "yellow_taxi",
            SILVER_DIR / "yellow_taxi",
            GOLD_DIR / "daily_metrics",
            GOLD_DIR / "zone_metrics",
            GOLD_DIR / "payment_metrics",
        ]
        success_markers = {
            str(path.relative_to(Path(__file__).resolve().parents[1])): (path / "_SUCCESS").is_file()
            for path in expected_paths
        }
        print(f"success_markers={success_markers}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
