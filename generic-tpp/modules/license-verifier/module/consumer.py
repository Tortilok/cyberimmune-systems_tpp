import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver
from .libs import AESCipher


MODULE_NAME = os.getenv('MODULE_NAME')


def return_error(details):
    details['deliver_to'] = 'task-scheduler'
    details['operation'] = 'send_message'
    details['message'] = 'failed to login'
    details['status'] = '403'
    proceed_to_deliver(details['id'], details)
    print('Ошибка проверки данных пользователя')


def handle_event(id, details_str):
    details = json.loads(details_str)
    print(f"[info] handling event {id}, " \
          f"{details['source']}->{details['deliver_to']}: " \
          f"{details['operation']}")
    
    # Получаем креды
    login = details.get('login')
    role = details.get('role')
    user_license = details.get('license')

    with open('/module/data/secret-licenses.json') as file:
        users_data = json.load(file)

    # Нет такого пользователя
    current_user_license = users_data.get(login)
    if not current_user_license:
        print('Нет пользователя')
        return return_error(details)
    
    # Или неправильная лицензия
    try:
        cipher = AESCipher(current_user_license)
        if cipher.decrypt(user_license) != role:
            return return_error(details)
    except:
        print('Ошибка в дешифрации')
        return return_error(details)

    details['deliver_to'] = 'task-scheduler'
    details['authorized'] = True
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
