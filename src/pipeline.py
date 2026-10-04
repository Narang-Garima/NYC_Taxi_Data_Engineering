from pathlib import Path
from pyspark.sql import DataFrame, functions as F

from .quality import validate_required_columns, quality_summary

def read_raw(spark, input_path: str) -> DataFrame:
    """Read NYC TLC Parquet using Spark's native Parquet reader."""
    df = spark.read.parquet(input_path)
    validate_required_columns(df)
    return df

def build_bronze(df: DataFrame) -> DataFrame:
    """Preserve source columns and add ingestion metadata."""
    return (
        df.withColumn("_ingested_at", F.current_timestamp())
          .withColumn("_source_file", F.input_file_name())
    )

def build_silver(df: DataFrame) -> DataFrame:
    """
    Create a clean analytical trip layer.
    Rules are intentionally transparent rather than silently imputing business fields.
    """
    validate_required_columns(df)

    duration_minutes = (
        F.unix_timestamp("tpep_dropoff_datetime")
        - F.unix_timestamp("tpep_pickup_datetime")
    ) / F.lit(60.0)

    cleaned = (
        df
        .filter(F.col("tpep_pickup_datetime").isNotNull())
        .filter(F.col("tpep_dropoff_datetime").isNotNull())
        .filter(F.col("tpep_dropoff_datetime") > F.col("tpep_pickup_datetime"))
        .filter(F.col("trip_distance") > 0)
        .filter(F.col("trip_distance") <= 100)
        .filter(F.col("fare_amount") >= 0)
        .filter(F.col("total_amount") >= 0)
        .filter(F.col("PULocationID").isNotNull())
        .filter(F.col("DOLocationID").isNotNull())
        .withColumn("trip_duration_minutes", duration_minutes)
        .filter(F.col("trip_duration_minutes").between(1, 240))
        .withColumn("pickup_date", F.to_date("tpep_pickup_datetime"))
        .withColumn("pickup_hour", F.hour("tpep_pickup_datetime"))
        .withColumn("pickup_year", F.year("tpep_pickup_datetime"))
        .withColumn("pickup_month", F.month("tpep_pickup_datetime"))
        .withColumn(
            "average_speed_mph",
            F.round(F.col("trip_distance") / (F.col("trip_duration_minutes") / 60.0), 2)
        )
        .filter(F.col("average_speed_mph").between(0.1, 80))
    )
    return cleaned

def build_gold(silver: DataFrame):
    """Create business-friendly aggregate tables from the curated trip layer."""
    daily = (
        silver.groupBy("pickup_date")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.avg("trip_distance"), 2).alias("avg_trip_distance"),
            F.round(F.avg("trip_duration_minutes"), 2).alias("avg_trip_duration_minutes"),
            F.round(F.sum("total_amount"), 2).alias("gross_total_amount"),
            F.round(F.avg("tip_amount"), 2).alias("avg_tip_amount"),
        )
        .orderBy("pickup_date")
    )

    zones = (
        silver.groupBy("PULocationID")
        .agg(
            F.count("*").alias("pickup_trip_count"),
            F.round(F.avg("trip_distance"), 2).alias("avg_trip_distance"),
            F.round(F.avg("total_amount"), 2).alias("avg_total_amount"),
        )
        .orderBy(F.desc("pickup_trip_count"))
    )

    payments = (
        silver.groupBy("payment_type")
        .agg(
            F.count("*").alias("trip_count"),
            F.round(F.avg("total_amount"), 2).alias("avg_total_amount"),
            F.round(F.sum("tip_amount"), 2).alias("total_tips"),
        )
        .orderBy(F.desc("trip_count"))
    )
    return daily, zones, payments

def write_layers(bronze, silver, daily, zones, payments, base_dir: str) -> None:
    base = Path(base_dir)
    bronze.write.mode("overwrite").parquet(str(base / "bronze" / "yellow_taxi"))
    (
        silver.write.mode("overwrite")
        .partitionBy("pickup_year", "pickup_month")
        .parquet(str(base / "silver" / "yellow_taxi"))
    )
    daily.write.mode("overwrite").parquet(str(base / "gold" / "daily_metrics"))
    zones.write.mode("overwrite").parquet(str(base / "gold" / "zone_metrics"))
    payments.write.mode("overwrite").parquet(str(base / "gold" / "payment_metrics"))

def run_pipeline(spark, input_path: str, data_dir: str):
    raw = read_raw(spark, input_path)
    before = quality_summary(raw)
    bronze = build_bronze(raw)
    silver = build_silver(bronze)
    after = quality_summary(silver)
    daily, zones, payments = build_gold(silver)
    write_layers(bronze, silver, daily, zones, payments, data_dir)
    return {"before": before, "after": after, "silver": silver,
            "daily": daily, "zones": zones, "payments": payments}
