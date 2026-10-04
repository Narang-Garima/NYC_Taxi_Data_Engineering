-- Register the Silver Parquet dataset as a Spark SQL temp view named yellow_taxi_silver
-- before running these queries.

-- 1. Peak pickup hours
SELECT
    pickup_hour,
    COUNT(*) AS trip_count
FROM yellow_taxi_silver
GROUP BY pickup_hour
ORDER BY trip_count DESC;

-- 2. Busiest pickup zones
SELECT
    PULocationID,
    COUNT(*) AS trip_count,
    ROUND(AVG(trip_distance), 2) AS avg_trip_distance,
    ROUND(AVG(total_amount), 2) AS avg_total_amount
FROM yellow_taxi_silver
GROUP BY PULocationID
ORDER BY trip_count DESC
LIMIT 20;

-- 3. Daily operational trend
SELECT
    pickup_date,
    COUNT(*) AS trip_count,
    ROUND(AVG(trip_duration_minutes), 2) AS avg_duration_minutes,
    ROUND(SUM(total_amount), 2) AS gross_total_amount
FROM yellow_taxi_silver
GROUP BY pickup_date
ORDER BY pickup_date;

-- 4. Payment-type behavior
SELECT
    payment_type,
    COUNT(*) AS trip_count,
    ROUND(AVG(total_amount), 2) AS avg_total_amount,
    ROUND(SUM(tip_amount), 2) AS total_tips
FROM yellow_taxi_silver
GROUP BY payment_type
ORDER BY trip_count DESC;
