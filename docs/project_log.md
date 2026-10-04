# Project Build Log

## Goal
Build a portfolio project that demonstrates a different skill set from small Pandas/BI projects:
PySpark, layered data design, Parquet, data-quality rules, partitioning, Spark SQL, and tests.

## Implemented
- Native Spark Parquet ingestion.
- Bronze source-preserving layer with ingestion metadata.
- Required-column validation and quality summary.
- Silver cleaning and feature engineering.
- Year/month partitioned Silver Parquet.
- Gold daily, pickup-zone, and payment aggregates.
- Spark SQL analysis examples.
- PySpark unit tests with synthetic records.
- Architecture and data-quality documentation.
- README with official NYC TLC source attribution.

## Intentionally not claimed
- No cloud platform deployment.
- No Databricks/Snowflake/ADF claim.
- No benchmark or performance-improvement percentage.
- No claim that project thresholds are official TLC rules.
- No fabricated production scale result.

## Next optional extension
Join TLC Taxi Zone lookup data so zone IDs can be reported as borough/zone names.

## 2026-10-03 Windows validation

Resolved the local Windows Hadoop/winutils configuration and completed a real pipeline, test, and output read-back validation. See `docs/windows_pyspark_resolution.md` for the complete command history, environment changes, failures, fixes, checksums, actual row counts, data-quality results, and test evidence.
