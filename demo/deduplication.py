def deduplicate_events(df):

    return (
        df
        .dropDuplicates(["event_id"])
    )