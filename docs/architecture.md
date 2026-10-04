# Architecture

```text
NYC TLC Yellow Taxi monthly Parquet
                |
                v
        PySpark ingestion
                |
                v
+----------------------------------+
| BRONZE                           |
| source-preserving Parquet        |
| + ingestion timestamp/source     |
+----------------------------------+
                |
                v
      Data-quality validation
                |
                v
+----------------------------------+
| SILVER                           |
| valid timestamps                 |
| valid distance/fare rules        |
| duration/date/hour features      |
| average speed feature            |
| partitioned by year/month        |
+----------------------------------+
                |
                v
+----------------------------------+
| GOLD                             |
| daily_metrics                    |
| zone_metrics                     |
| payment_metrics                  |
+----------------------------------+
                |
                v
         Spark SQL analysis
```

## Why this design?

The project separates source preservation, curated trip-level data, and downstream aggregates.
That makes the transformations easier to audit and keeps analytical consumers away from raw records.

This is a local portfolio implementation of layered data engineering.
