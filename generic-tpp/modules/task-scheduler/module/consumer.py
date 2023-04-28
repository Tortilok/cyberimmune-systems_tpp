import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME = os.getenv('MODULE_NAME')


def handle_event(id, details_str):
    details = json.loads(details_str)
    print(f"[info] handling event {id}, " \
          f"{details['source']}->{details['deliver_to']}: " \
          f"{details['operation']}")
    
    operation = details.get('operation')

    # Проверка авторизации
    authorized = False
    if details.get('authorized'):
        authorized = True

    # Если срочно нужно отдать сообщение
    if operation == 'send_message':
        details['deliver_to'] = 'command-block'
        return proceed_to_deliver(id, details)

    if not authorized:
        # Отправляем проходить процесс проверки
        details['deliver_to'] = 'authorization-verifier'
        return proceed_to_deliver(id, details)

    if operation == 'turbine_stop':
        details['deliver_to'] = 'command-block'
        return proceed_to_deliver(id, details)
    elif operation == 'turbine_start':
        details['deliver_to'] = 'command-block'
        return proceed_to_deliver(id, details)
    elif operation == 'check_sensors':
        details['deliver_to'] = 'command-block'
        return proceed_to_deliver(id, details)
    elif operation == 'update_app':
        details['deliver_to'] = 'update-manager'
        details['operation'] = 'verify_app'
        return proceed_to_deliver(id, details)
    elif operation == 'update_settings':
        details['deliver_to'] = 'update-manager'
        return proceed_to_deliver(id, details)

    details['operation'] = 'send_message'
    details['message'] = 'ok!'
    details['deliver_to'] = 'command-block'
    proceed_to_deliver(id, details)


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
                # Extract the (optional) key and value, and print.
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