import os
import json
import threading

from time import sleep
from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


MODULE_NAME = os.getenv('MODULE_NAME')


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


def send_wait(details):
    details = clear_details(details)
    details['operation'] = 'wait'
    details['deliver_to'] = 'data-verifier'
    return proceed_to_deliver(details['id'], details)


def get_sensors():
    with open('/module/data/analog.json', 'r') as analog_file:
        analog_data = json.load(analog_file)
    with open('/module/data/discrete.txt', 'r') as discrete_file:
        discrete_data = discrete_file.read()
    if len(discrete_data) > 10:
        print('Обрезаем длинные дискретные данные')
        discrete_data = discrete_data[:10]
    elif len(discrete_data) < 10:
        print('Длина дискретных данных слишком мала')
        return None
    
    return (analog_data, discrete_data)


def handle_event(id, details_str):
    details = json.loads(details_str)
    print(f"[info] handling event {id}, " \
          f"{details['source']}->{details['deliver_to']}: " \
          f"{details['operation']}")

    if details['operation'] == 'store_analog':
        with open('/module/data/analog.json', 'w') as analog_file:
            analog_file.write(json.dumps(details.get('data', {})))
        return

    if details['operation'] == 'store_discrete':
        data_to_write = str(details.get('data', {}).get('value', 0))
        with open('/module/data/discrete.txt', 'a+') as discrete_file:
            discrete_file.seek(0)
            data = discrete_file.read()
            if len(data) > 50:
                discrete_file.seek(0)
                discrete_file.truncate()
            discrete_file.write(data_to_write)
        return
    
    if details['operation'] == 'get_data':
        print('Запрос на получение данных')
        sensors = get_sensors()
        while not sensors:
            sleep(2)
            print('Ждём наполнения...')
            sensors = get_sensors()
        analog_data, discrete_data = sensors
        
        details['analog_data_storage'] = analog_data
        details['discrete_data_storage'] = discrete_data
        details['deliver_to'] = 'data-verifier'
        details['operation'] = 'verify_data'

        return proceed_to_deliver(id, details)

    if details['operation'] == 'clear_data':
        with open('/module/data/analog.json', 'w') as analog_file:
            analog_file.write('')
        with open('/module/data/discrete.txt', 'w') as discrete_file:
            discrete_file.write('')
        details = clear_details(details)
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
