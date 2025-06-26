"""https://medium.com/@arturocuicas/fastapi-and-apache-kafka-4c9e90aab27f"""

import asyncio
import json
import os
from random import shuffle
from typing import List

from aiokafka import AIOKafkaConsumer
from aiokafka import AIOKafkaProducer
from dotenv import load_dotenv
from fastapi import FastAPI
import structlog
from tenacity import retry
from tenacity import stop_after_attempt


logger = structlog.get_logger()


app = FastAPI()
load_dotenv()


loop = asyncio.get_event_loop()

spidey_names: List[str] = os.environ.get("SPIDEY_NAMES").split(",")
kafka_bootstrap_servers: str = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
spiderweb_topic: str = os.environ.get("SPIDERWEB_TOPIC")
my_name: str = os.environ.get("MY_NAME")

mapping_place = {
    3: "name is the Winner!!!",
    2: "name is the Second Place!!!",
    1: "name is the third Place!!!",
}


def spidey_random(spidey_list: List) -> List:
    shuffle(spidey_list)
    return spidey_list


async def play_turn(finalists: List):
    spidey_order = spidey_random(finalists)
    await send_one(topic=spiderweb_topic, msg=spidey_order)


def kafka_serializer(value):
    return json.dumps(value).encode()


def encode_json(msg):
    to_load = msg.value.decode("utf-8")
    return json.loads(to_load)


def check_spidey(finalists: List) -> bool:
    return my_name == finalists[0]

@retry(stop=stop_after_attempt(3))
async def send_one(topic: str, msg: List):
    try:
        async with AIOKafkaProducer(
                bootstrap_servers=kafka_bootstrap_servers,
                # Built-in serialization
                value_serializer=lambda v: json.dumps(v).encode(),
                request_timeout_ms=5000,
        ) as producer:
            await producer.send_and_wait(topic, msg)

    except Exception as err:
        print(f"Some Kafka error: {err}")

async def spiderweb_turn(msg):
    try:
        finalists = encode_json(msg)
        if not validate_game_state(finalists):
            return

        if my_name == finalists[0]:
            placement = len(finalists)
            logger.info("I won this round!", placement=placement)
            print(mapping_place[placement].replace("name", my_name))

            if len(finalists) > 1:
                await play_turn(finalists[1:])  # Pass remaining players
    except Exception as e:
        logger.error("Turn processing failed", error=str(e))

def validate_game_state(finalists: List[str]) -> bool:
    if not finalists:
        logger.error("Empty finalists list!")
        return False
    if my_name not in finalists:
        logger.warning("I'm not in this round!", my_name=my_name)
        return False
    return True

kafka_actions = {
    "spiderweb": spiderweb_turn,
}


async def consume():
    consumer = AIOKafkaConsumer(
        spiderweb_topic,
        loop=loop,
        bootstrap_servers=kafka_bootstrap_servers,
        group_id=f"spiderweb-{my_name}", # Prevents duplicate processing
    )

    try:
        await consumer.start()

    except Exception as e:
        print(e)
        return

    try:
        async for msg in consumer:
            await kafka_actions[msg.topic](msg)

    finally:
        await consumer.stop()


asyncio.create_task(consume())


@app.get("/")
async def root():
    return {"Kafka": "Spiderweb"}


@app.get("/start")
async def start_game():
    spidey_order = spidey_random(spidey_names)
    logger.info("Game started", init_order=spidey_order)
    await send_one(topic=spiderweb_topic, msg=spidey_order)
    return {"order": spidey_order}


@app.get("/health")
async def health():
    return {"status": "alive", "my_name": my_name}
