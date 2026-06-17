from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import sys

sys.path.append(".")

from test_schemas import login_event_schema
from validation import validate_login_events
from deduplication import deduplicate_events
from console_sink import write_console


spark = (
    SparkSession.builder
    .appName("LoginEventJob")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

raw_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "test.ioe.login_events")
    .option("startingOffsets", "latest")
    .load()
)

json_df = (
    raw_df
    .selectExpr("CAST(value AS STRING)")
)

parsed_df = (
    json_df
    .select(
        from_json(
            col("value"),
            login_event_schema
        ).alias("event")
    )
    .select("event.*")
)

validated_df = validate_login_events(parsed_df)

dedup_df = deduplicate_events(validated_df)

query = write_console(dedup_df)

query.awaitTermination()