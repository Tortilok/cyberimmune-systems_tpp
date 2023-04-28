import os
import json
import threading

from time import sleep
from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME = os.getenv('MODULE_NAME')


def send_to_storage(details):
    details['operation'] = 'get_data'
    details['deliver_to'] = 'data-storage'
    print('Отправлено в storage')
    proceed_to_deliver(details['id'], details)


def send_to_app(details):
    details['operation'] = 'get_data'
    details['deliver_to'] = 'app'
    print('Отправлено в ПП', details)
    proceed_to_deliver(details['id'], details)


def clear_data(details):
    details['operation'] = 'clear_data'
    details['deliver_to'] = 'app'
    proceed_to_deliver(details['id'], details)
    details['deliver_to'] = 'data-storage'
    proceed_to_deliver(details['id'], details)


def clear_details(details):
    if details.get('analog_data_storage'):
        del details['analog_data_storage']
    if details.get('discrete_data_storage'):
        del details['discrete_data_storage']
    if details.get('analog_data_app'):
        del details['analog_data_app']
    if details.get('discrete_data_app'):
        del details['discrete_data_app']

    return details


def check_data(details):
    analog_data_storage = details.get('analog_data_storage')
    discrete_data_storage = details.get('discrete_data_storage')
    analog_data_app = details.get('analog_data_app')
    discrete_data_app = details.get('discrete_data_app')

    if len(discrete_data_storage) > 10:
        discrete_data_storage = discrete_data_storage[:10]
    if len(discrete_data_app) > 10:
        discrete_data_app = discrete_data_app[:10]

    if not all((analog_data_storage, discrete_data_storage)):
        print('Нет данных с хранилища')
        send_to_storage(details)
        return False

    if not all((analog_data_app, discrete_data_app)):
        print('Нет данных из ПП')
        send_to_storage(details)
        return False

    if analog_data_storage != analog_data_app:
        print('Аналоговые данные не равны')
        clear_data(details)
        return False

    if discrete_data_storage != discrete_data_app:
        print('Дискретные данные не равны')
        clear_data(details)
        return False
    
    return True


def send_message(details):
    details['operation'] = 'send_message'
    details['deliver_to'] = 'command-block'
    analog_sensors = details.get('analog_data') or details['analog_data_app']
    discrete_sensors = details.get('discrete_data') or \
                       details['discrete_data_app']
    is_critical = details.get('is_critical', True)
    details['message'] = {
        'analog_sensors': json.loads(analog_sensors),
        'discrete_sensors': [discrete_sensors],
        'is_critical': is_critical
    }
    proceed_to_deliver(details['id'], details)


def handle_event(id, details_str):
    details = json.loads(details_str)
    print(f"[info] handling event {id}, " \
          f"{details['source']}->{details['deliver_to']}: " \
          f"{details['operation']}")

    # Отправляем на сбор данных
    if details['operation'] == 'verify':
        send_to_app(details)
        # send_to_storage(details)
    
    if details['operation'] == 'verify_data':
        # for _ in range(150):
        #     sleep(0.5)
        #     if all((details.get('analog_data_storage'),
        #             details.get('analog_data_app')),
        #             details.get('discrete_data_storage'),
        #             details.get('discrete_data_app')):
        #         print('DONE!')
        #         break
        for _ in range(150):
            sleep(0.5)
            if all((details.get('analog_data_app'),
                    details.get('discrete_data_app'))):
                send_message(details)
                return
            
        details['operation'] = 'send_message'
        details['deliver_to'] = 'command-block'
        details['message'] = {
            'message': 'sensors not working',
            'is_critical': True
        }
        proceed_to_deliver(details['id'], details)
        


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
