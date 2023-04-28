import os
import json
import threading
import multiprocessing

from confluent_kafka import Producer


_requests_queue: multiprocessing.Queue = None
MODULE_NAME = os.getenv('MODULE_NAME')


def proceed_to_deliver(id, details):
    _requests_queue.put(details)


def producer_job(_, config, requests_queue: multiprocessing.Queue):
    producer = Producer(config)

    def delivery_callback(err, msg):
        if err:
            print('[error] Message failed delivery: {}'.format(err))

    while True:
        event_details = requests_queue.get()
        print(event_details)     
        topic = event_details['deliver_to']
        producer.produce(
            topic,
            json.dumps(event_details),
            event_details['id'],  
            callback=delivery_callback
        )

        producer.poll(10000)
        producer.flush()


def start_producer(args, config, requests_queue):
    print(f'{MODULE_NAME}_producer started')

    global _requests_queue

    _requests_queue = requests_queue
    threading.Thread(
        target=lambda: producer_job(args, config, requests_queue)
    ).start()
