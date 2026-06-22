import requests
import os
from dotenv import load_dotenv

load_dotenv(".env.dev")

CLICKHOUSE_HTTP_URL = os.getenv("CLICKHOUSE_HTTP_URL", "http://localhost:8123")
CLICKHOUSE_USER     = os.getenv("CLICKHOUSE_USER", "admin")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "admin123")
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "realtime")


def write_to_clickhouse(batch_df, batch_id):
    rows = batch_df.toJSON().collect()

    if not rows:
        print(f"Batch {batch_id} skipped: empty")
        return

    response = requests.post(
        f"{CLICKHOUSE_HTTP_URL}/",
        params={
            "query": f"INSERT INTO {CLICKHOUSE_DATABASE}.login_events FORMAT JSONEachRow",
            "date_time_input_format": "best_effort",
        },
        data="\n".join(rows),
        auth=(CLICKHOUSE_USER, CLICKHOUSE_PASSWORD),
        timeout=30,
    )

    response.raise_for_status()

    print(f"Batch {batch_id} written: {len(rows)} rows")
