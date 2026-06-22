from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import yaml
import os
from dotenv import load_dotenv

load_dotenv(".env.dev")

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
if not BOOTSTRAP_SERVERS:
    raise ValueError("KAFKA_BOOTSTRAP_SERVERS is not configured")


def load_topics():
    with open("/home/huongdt/Data_02/demo/topics.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config["topics"]


def main():

    admin = KafkaAdminClient(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        client_id="topic-manager"
    )

    existing_topics = admin.list_topics()

    topics_to_create = []

    for topic in load_topics():

        topic_name = topic["name"]

        if topic_name in existing_topics:
            print(f"[SKIP] {topic_name} already exists")
            continue

        topics_to_create.append(
            NewTopic(
                name=topic_name,
                num_partitions=topic["partitions"],
                replication_factor=topic["replication_factor"]
            )
        )

    if topics_to_create:

        admin.create_topics(
            new_topics=topics_to_create,
            validate_only=False
        )

        for topic in topics_to_create:
            print(f"[CREATE] {topic.name}")

    else:
        print("No new topics to create")

    admin.close()


if __name__ == "__main__":
    main()