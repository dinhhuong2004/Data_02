from pyspark.sql.types import IntegerType, StringType, StructField, StructType, TimestampType

login_event_schema = StructType([
    StructField("event_id", StringType(), nullable=False),
    StructField("event_name", StringType(), nullable=False),
    StructField("event_time", TimestampType(), nullable=False),

    StructField("userid", StringType(), nullable=False),
    StructField("username", StringType(), nullable=False),

    StructField("location_id", IntegerType(), nullable=False),
    StructField("acc_type", IntegerType(), nullable=False)
])
