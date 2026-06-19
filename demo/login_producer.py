from kafka import KafkaProducer
import json
import uuid
import random
import time

from collections import defaultdict, deque
from datetime import datetime, timezone


producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    api_version=(3, 5, 0),
    value_serializer=lambda x: json.dumps(x).encode("utf-8")
)

TOPIC = "test.ioe.login_events"

USER_COUNT = 1000

users = []

for i in range(USER_COUNT):

    userid = str(1000000000 + i)

    users.append({
        "userid": userid,
        "username": f"user_{userid}"
    })


# ------------------------------------------------------------------
# USER WEIGHTS
# ------------------------------------------------------------------

user_weights = []

for idx in range(USER_COUNT):

    if idx < 100:
        # power users
        user_weights.append(random.randint(80, 120))

    elif idx < 400:
        # active users
        user_weights.append(random.randint(20, 60))

    else:
        # normal users
        user_weights.append(random.randint(1, 10))


# ------------------------------------------------------------------
# LOGIN HISTORY
# user -> timestamps in last hour
# ------------------------------------------------------------------

login_history = defaultdict(deque)

MAX_LOGIN_PER_HOUR = 10

LOCATIONS = list(range(1, 35))
ACC_TYPES = [1, 2, 3, 4, 5]


def is_peak_hour():

    hour = datetime.now().hour

    return (
        7 <= hour <= 9 or
        13 <= hour <= 15 or
        19 <= hour <= 22
    )


def select_user():

    while True:

        user = random.choices(
            users,
            weights=user_weights,
            k=1
        )[0]

        now_ts = time.time()

        history = login_history[user["userid"]]

        while history and now_ts - history[0] > 3600:
            history.popleft()

        if len(history) < MAX_LOGIN_PER_HOUR:
            history.append(now_ts)
            return user


while True:

    now = datetime.now(timezone.utc)

    user = select_user()

    event = {
        "event_id": str(uuid.uuid4()),
        "event_name": "ioe.login",
        "event_time": now.isoformat(),

        "userid": user["userid"],
        "username": user["username"],

        "location_id": random.randint(1, 34),

        "acc_type": random.randint(1, 5)
    }

    future = producer.send(
        TOPIC,
        value=event,
        timestamp_ms=int(now.timestamp() * 1000)
    )

    metadata = future.get(timeout=10)

    print(
        f"[{now.strftime('%H:%M:%S')}] "
        f"user={event['userid']} "
        f"loc={event['location_id']} "
        f"acc={event['acc_type']} "
        f"partition={metadata.partition} "
        f"offset={metadata.offset}"
    )

    # ------------------------------------------------------------------
    # Traffic model
    # ------------------------------------------------------------------

    if is_peak_hour():

        sleep_time = random.uniform(
            0.05,
            0.4
        )

    else:

        sleep_time = random.uniform(
            0.3,
            2.0
        )

    # burst traffic
    if random.random() < 0.08:

        burst_size = random.randint(3, 10)

        for _ in range(burst_size):

            burst_user = select_user()

            burst_event = {
                "event_id": str(uuid.uuid4()),
                "event_name": "ioe.login",
                "event_time": datetime.now(
                    timezone.utc
                ).isoformat(),

                "userid": burst_user["userid"],
                "username": burst_user["username"],

                "location_id": random.randint(1, 34),
                "acc_type": random.randint(1, 5)
            }

            producer.send(
                TOPIC,
                value=burst_event
            )

    producer.flush()

    time.sleep(sleep_time)