from datetime import datetime
from src.pipeline import build_silver, build_gold

def _sample_df(spark):
    rows = [
        (datetime(2025,1,1,8,0), datetime(2025,1,1,8,30), 1, 2, 5.0, 20.0, 25.0, 4.0, 1),
        (datetime(2025,1,1,9,0), datetime(2025,1,1,8,50), 1, 2, 2.0, 10.0, 12.0, 2.0, 1),
        (datetime(2025,1,1,10,0), datetime(2025,1,1,10,20), 3, 4, -1.0, 10.0, 12.0, 1.0, 2),
    ]
    cols = [
        "tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID",
        "DOLocationID", "trip_distance", "fare_amount", "total_amount",
        "tip_amount", "payment_type"
    ]
    return spark.createDataFrame(rows, cols)

def test_silver_filters_invalid_records(spark):
    silver = build_silver(_sample_df(spark))
    assert silver.count() == 1
    row = silver.first()
    assert row.trip_duration_minutes == 30.0
    assert row.pickup_hour == 8

def test_gold_daily_aggregate(spark):
    silver = build_silver(_sample_df(spark))
    daily, zones, payments = build_gold(silver)
    assert daily.first().trip_count == 1
    assert zones.first().pickup_trip_count == 1
    assert payments.first().trip_count == 1
