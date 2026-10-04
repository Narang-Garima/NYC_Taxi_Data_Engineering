import pytest
from src.spark_session import get_spark

@pytest.fixture(scope="session")
def spark():
    spark = get_spark("nyc-taxi-tests")
    spark.conf.set("spark.sql.shuffle.partitions", "2")
    yield spark
    spark.stop()
