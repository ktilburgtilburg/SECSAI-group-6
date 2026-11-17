"""Stand-in model worker for testing the interface server."""

import json
import os
import time

import pika

URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE = "assess_requests"


def on_request(ch, method, props, body):
    url = json.loads(body)["url"]
    if "slow" in url:
        time.sleep(3)  # longer than the 2 s timeout -> expect 504
    if "garbage" in url:
        reply = b"not json"  # -> expect 502
    else:
        bad = "login" in url
        reply = json.dumps(
            {
                "is_malicious": bad,
                "category": "phishing" if bad else "benign",
                "confidence": 0.85,
                "explanations": ["Contains credential keywords"] if bad else [],
                "worker_id": "fake-1",
            }
        ).encode()
    ch.basic_publish(
        exchange="",
        routing_key=props.reply_to,
        body=reply,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)


conn = pika.BlockingConnection(pika.URLParameters(URL))
channel = conn.channel()
channel.queue_declare(queue=QUEUE)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=QUEUE, on_message_callback=on_request)
print("fake worker waiting for requests...")
channel.start_consuming()
