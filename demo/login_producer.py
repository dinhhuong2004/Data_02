from kafka import KafkaProducer
import json
import uuid
import time
import random
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda x: json.dumps(x).encode("utf-8")
)

while True:

    event_type = random.choice([
        "login",
        "logout"
    ])

    event = {
        "event_id": str(uuid.uuid4()),
        "event_name": event_type,
        "event_time": datetime.utcnow().isoformat(),
        "user_id": random.randint(1, 1000)
    }

    topic = (
        "test.ioe.login_events"
        if event_type == "login"
        else "test.ioe.logout_events"
    )

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

    time.sleep(1)