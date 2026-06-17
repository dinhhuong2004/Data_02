from pyspark.sql.types import *

login_event_schema = StructType([
    StructField("event_id", StringType()),
    StructField("event_name", StringType()),
    StructField("event_time", StringType()),
    StructField("user_id", LongType()),
    # StructField("device_type", StringType())
])