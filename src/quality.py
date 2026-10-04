from pyspark.sql import DataFrame, functions as F

REQUIRED_COLUMNS = {
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "trip_distance",
    "fare_amount",
    "total_amount",
}

def validate_required_columns(df: DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

def quality_summary(df: DataFrame) -> DataFrame:
    """Return one-row data-quality metrics without collecting the full dataset."""
    validate_required_columns(df)
    return df.agg(
        F.count("*").alias("row_count"),
        F.sum(F.when(F.col("tpep_pickup_datetime").isNull(), 1).otherwise(0)).alias("null_pickup"),
        F.sum(F.when(F.col("tpep_dropoff_datetime").isNull(), 1).otherwise(0)).alias("null_dropoff"),
        F.sum(F.when(F.col("trip_distance") <= 0, 1).otherwise(0)).alias("nonpositive_distance"),
        F.sum(F.when(F.col("total_amount") < 0, 1).otherwise(0)).alias("negative_total"),
        F.sum(
            F.when(F.col("tpep_dropoff_datetime") <= F.col("tpep_pickup_datetime"), 1).otherwise(0)
        ).alias("invalid_time_order"),
    )
