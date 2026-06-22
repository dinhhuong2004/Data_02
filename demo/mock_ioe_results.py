import uuid
import random
import pandas as pd

from datetime import datetime
from datetime import timedelta

NUM_USERS = 1000
TARGET_RECORDS = 15000

START_TIME = datetime(2026, 6, 18, 0, 0, 0)
END_TIME = datetime(2026, 6, 19, 23, 59, 59)

devices = ["web", "android", "ios"]
device_weights = [40, 45, 15]

# ---------------------------------------------------
# User dimension
# ---------------------------------------------------

users = []

for i in range(NUM_USERS):

    user_id = str(1000000000 + i)

    grade = random.randint(1, 12)

    if grade <= 5:
        edu_level = "Tiểu học"
        school_id = f"{random.randint(1,1000):04d}"

    elif grade <= 9:
        edu_level = "THCS"
        school_id = f"{random.randint(1001,2000):04d}"

    else:
        edu_level = "THPT"
        school_id = f"{random.randint(2001,3000):04d}"

    users.append(
        {
            "user_id": user_id,
            "user_name": f"user_{user_id}",
            "grade": grade,
            "edu_level": edu_level,
            "school_id": school_id,
            "province_id": random.randint(1, 34),
            "village_id": random.randint(100, 1000),
        }
    )

# ---------------------------------------------------
# Generate submissions
# ---------------------------------------------------

rows = []

while len(rows) < TARGET_RECORDS:

    user = random.choice(users)

    rounds = random.sample(range(1, 11), random.randint(1, 10))

    for round_num in rounds:

        submit_count = random.randint(1, 2)

        for _ in range(submit_count):

            if len(rows) >= TARGET_RECORDS:
                break

            seconds = random.randint(
                0,
                int((END_TIME - START_TIME).total_seconds())
            )

            event_time = START_TIME + timedelta(seconds=seconds)

            score_bucket = random.random()

            if score_bucket < 0.7:
                score = random.randrange(500, 801, 10)

            elif score_bucket < 0.9:
                score = random.randrange(300, 500, 10)

            else:
                score = random.randrange(810, 1001, 10)

            total_time = random.randint(1800, 3600)

            rows.append(
                {
                    "event_id": str(uuid.uuid4()),
                    "event_name": "submit_result",

                    "user_id": user["user_id"],
                    "user_name": user["user_name"],

                    "event_time": event_time.strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                    )[:-4],

                    "round_num": round_num,

                    "total_score": score,

                    "total_time": total_time,

                    "device": random.choices(
                        devices,
                        weights=device_weights,
                        k=1
                    )[0],

                    "province_id": user["province_id"],

                    "village_id": user["village_id"],

                    "school_id": user["school_id"],

                    "grade": user["grade"],

                    "edu_level": user["edu_level"]
                }
            )

df = pd.DataFrame(rows)

df.to_csv(
    "submit_result_events_15000.csv",
    index=False,
    encoding="utf-8-sig"
)

print(df.shape)
print(df.head())