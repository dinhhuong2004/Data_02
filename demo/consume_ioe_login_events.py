from pyspark.sql import SparkSession
# input: login events từ Kafka topic "edu.login_events"
# output: in ra console
spark = (
    SparkSession.builder
    .appName("LoginEventConsumer")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "test.ioe.login_events")
    .option("startingOffsets", "latest")
    .load()
)
df.printSchema()

result = df.selectExpr(
    "CAST(value AS STRING) as json_payload"
)

query = (
    result.writeStream
    .format("console")
    .outputMode("append")
    .start()
)

query.awaitTermination()
