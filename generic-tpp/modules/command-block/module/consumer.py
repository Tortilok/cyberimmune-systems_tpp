import os
import json
import requests
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME = os.getenv('MODULE_NAME')


def handle_event(id, details_str):
    details = json.loads(details_str)
    print(f"[info] handling event {id}, " \
          f"{details['source']}->{details['deliver_to']}: " \
          f"{details['operation']}")

    if details['operation'] == 'send_message':
        details['deliver_to'] = 'scada-sender'
        # Если не получили статус сообщения
        details['status'] = details.get('status', 200)
        return proceed_to_deliver(id, details)
    
    if details['operation'] == 'turbine_stop':
        print('command-block -> stop turbine')

        response = requests.get('http://turbine:8001/stop')
        if response.status_code != 200:
            details['message'] = 'Turbine is not responding...'
        else:
            details['message'] = 'Turbine has been stopped!'
        details['operation'] = 'send_message'
        details['deliver_to'] = 'scada-sender'
        details['status'] = response.status_code

        return proceed_to_deliver(id, details)
    
    if details['operation'] == 'turbine_start':
        print('command-block -> start turbine')
        response = requests.get('http://turbine:8001/start')
        if response.status_code != 200:
            details['message'] = 'Turbine is not responding...'
        else:
            details['message'] = 'Turbine has been started!'
        details['operation'] = 'send_message'
        details['deliver_to'] = 'scada-sender'
        details['status'] = response.status_code
        
        return proceed_to_deliver(id, details)
    
    if details['operation'] == 'send_message':
        details['deliver_to'] = 'scada-sender'
        # Если не получили статус сообщения
        details['status'] = details.get('status', 200)
        return proceed_to_deliver(id, details)
    
    if details['operation'] == 'check_sensors':
        details['deliver_to'] = 'app'
        details['operation'] = 'check_sensors'
        return proceed_to_deliver(id, details)


def consumer_job(args, config):
    consumer = Consumer(config)

    def reset_offset(verifier_consumer, partitions):
        if not args.reset:
            return
        
        for p in partitions:
            p.offset = OFFSET_BEGINNING
        verifier_consumer.assign(partitions)

    topic = MODULE_NAME
    consumer.subscribe([topic], on_assign=reset_offset)

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                pass
            elif msg.error():
                print(f"[error] {msg.error()}")
            else:
                try:
                    id = msg.key().decode('utf-8')
                    details_str = msg.value().decode('utf-8')
                    handle_event(id, details_str)
                except Exception as e:
                    print(f"[error] Malformed event received from " \
                          f"topic {topic}: {msg.value()}. {e}")
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

def start_consumer(args, config):
    print(f'{MODULE_NAME}_consumer started')
    threading.Thread(target=lambda: consumer_job(args, config)).start()
