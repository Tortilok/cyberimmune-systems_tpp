import os
import json
import hashlib
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME = os.getenv('MODULE_NAME')


def get_sha256(data: str) -> str:
    return str(hashlib.sha256(data.encode('utf-8')).hexdigest())


def handle_event(id, details_str):
    details = json.loads(details_str)
    print(f"[info] handling event {id}, " \
          f"{details['source']}->{details['deliver_to']}: " \
          f"{details['operation']}")
    
    if details['operation'] == 'check_license':
        details['operation'] = 'get_file_content'
        details['deliver_to'] = 'app-storage'
        return proceed_to_deliver(id, details)
    if details['operation'] == 'send_file_content':
        sha256 = get_sha256(details.get('file_content', ''))
        if sha256 != details['app_license']:
            print('Всё хуйня')
            # details['operation'] = 'no_license'
            # details['deliver_to'] = 'app-sender'
            # return proceed_to_deliver(id, details)
        
        print('Обновляем')
        # details['operation'] = 'update_app'
        # details['deliver_to'] = 'app-updater'
        # return proceed_to_deliver(id, details)


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
