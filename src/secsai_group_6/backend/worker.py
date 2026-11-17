import pika
import json
import os
import logging
from secsai_group_6.ml.predict import predict
import time

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
QUEUE_NAME = "url_scans"



def retry_connection(max_tries=15, delay=2):

    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)

    for attempt in range(max_tries):
        try:
            connection = pika.BlockingConnection(parameters)
            return connection

        except pika.exceptions.AMQPConnectionError:
            if attempt < max_tries - 1:
                time.sleep(delay)
            else:
                raise

def on_request(ch, method, props, body):

    try:
        data = json.loads(body)
        url = data.get("url")
        verdict = predict(url)

    except Exception as e:
        verdict = {
            "error": "Prediction failed",
            "is_malicious": False,
            "category": "unknown",
            "confidence": 0.0,
            "explanations": ["Model error: " + str(e)]
        }

    ch.basic_publish(
        exchange="",
        routing_key= props.reply_to,
        properties = pika.BasicProperties(correlation_id=props.correlation_id),
        body=json.dumps(verdict))

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    print("[*] Warming up ML model...", flush=True)
    try:
        predict("https://example.com/")
        print("[*] Model warmed up successfully.", flush=True)
    except Exception as e:
        print(f"[*] Model warm-up notice: {e}", flush=True)

    connection = retry_connection()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_request)
    print(f"[*] Worker ready. Waiting for requests on '{QUEUE_NAME}'...", flush=True)
    channel.start_consuming()

if __name__ == "__main__":
    main()




