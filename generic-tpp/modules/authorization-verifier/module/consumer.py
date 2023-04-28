import os
import json
import threading

from confluent_kafka import Consumer, OFFSET_BEGINNING

from .producer import proceed_to_deliver


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
    
    login = details.get('login')
    password = details.get('password')

    with open('/module/data/secret-logins.json') as file:
        users_data = json.load(file)

    current_user = users_data.get(login)
    # Неверный логин или пароль
    if not current_user or current_user.get('password') != password:
        return return_error(details)
    
    role = current_user.get('role')
    opr = details['operation']
    
    is_allowed = False
    if role == 'operator' and opr in ('check_sensors', 'update_settings',
                                      'turbine_stop', 'turbine_start'):
        is_allowed = True
    elif role == 'spector' and opr == 'check_sensors':
        is_allowed = True
    elif role == 'engineer' and opr == 'update_app':
        is_allowed = True

    # Запретный плод
    if not is_allowed:
        return return_error(details)
    
    details['deliver_to'] = 'license-verifier'
    details['role'] = role
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
