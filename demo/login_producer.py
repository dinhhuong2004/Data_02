from kafka import KafkaProducer
import json
import uuid
import time
import random
from datetime import datetime, timezone

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda x: json.dumps(x).encode("utf-8")
)

topic = "test.ioe.login_events"

USER_POOL_SIZE = 350
HOT_USER_COUNT = 35

users = [
    {
        "userid": str(1000000000 + index),
        "username": f"user_{1000000000 + index}",
    }
    for index in range(USER_POOL_SIZE)
]

user_weights = [
    random.randint(20, 80) if index < HOT_USER_COUNT else random.randint(1, 8)
    for index in range(USER_POOL_SIZE)
]

locations = list(range(1, 35))
location_weights = [
    32 if location in {1, 4, 8, 12, 23, 34}
    else 16 if location in {2, 6, 10, 17, 27, 31}
    else random.randint(2, 9)
    for location in locations
]

account_types = [1, 2, 3, 4, 5]
account_type_weights = [45, 28, 14, 9, 4]

while True:

    user = random.choices(
        users,
        weights=user_weights,
        k=1
    )[0]

    event = {
        "event_id": str(uuid.uuid4()),
        "event_name": "login",
        "event_time": datetime.now(timezone.utc).isoformat(),
        "userid": user["userid"],
        "username": user["username"],
        "location_id": random.choices(
            locations,
            weights=location_weights,
            k=1
        )[0],
        "acc_type": random.choices(
            account_types,
            weights=account_type_weights,
            k=1
        )[0]
    }

    future = producer.send(
        topic,
        event
    )

    metadata = future.get(timeout=10)

    print(
        f"topic={metadata.topic} "   # topic name
        f"partition={metadata.partition} "   # partition number
        f"offset={metadata.offset}"     #
    )

    producer.flush()

    if random.random() < 0.12:
        time.sleep(random.uniform(0.02, 0.12))
    else:
        time.sleep(random.uniform(0.25, 1.8))
