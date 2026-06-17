def write_console(df):

    return (
        df.writeStream
        .format("console")
        .outputMode("append")
        .option("truncate", False)
        .start()
    )