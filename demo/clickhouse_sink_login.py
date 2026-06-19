import requests


def write_to_clickhouse(batch_df, batch_id):
    rows = batch_df.toJSON().collect()

    if not rows:
        print(f"Batch {batch_id} skipped: empty")
        return

    response = requests.post(
        "http://localhost:8123/",
        params={
            "query": "INSERT INTO realtime.login_events FORMAT JSONEachRow",
            "date_time_input_format": "best_effort",
        },
        data="\n".join(rows),
        auth=("admin", "admin123"),
        timeout=30,
    )

    response.raise_for_status()

    print(f"Batch {batch_id} written: {len(rows)} rows")
