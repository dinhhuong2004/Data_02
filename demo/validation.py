from pyspark.sql.functions import col

def validate_login_events(df):

    return (
        df
        .filter(col("event_id").isNotNull())
        .filter(col("userid").isNotNull())
        .filter(col("event_time").isNotNull())
    )