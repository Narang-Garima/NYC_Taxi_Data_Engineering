# Data Quality Rules

The Silver layer uses explicit, reviewable rules rather than silently imputing transactional fields.

| Check | Action |
|---|---|
| Missing pickup/drop-off timestamp | reject from Silver |
| Drop-off <= pickup | reject |
| trip_distance <= 0 or > 100 miles | reject |
| fare_amount < 0 | reject |
| total_amount < 0 | reject |
| Missing pickup/drop-off zone | reject |
| duration < 1 or > 240 minutes | reject |
| calculated speed < 0.1 or > 80 mph | reject |

These thresholds are portfolio/business rules for this project, not official TLC validity rules.
The Bronze layer preserves the source data before these rules are applied.
