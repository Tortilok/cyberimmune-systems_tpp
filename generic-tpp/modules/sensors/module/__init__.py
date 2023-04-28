import os
import requests

from threading import Thread
from time import sleep

from .api import start_web


MODULE_NAME = os.getenv('MODULE_NAME')
SLEEP_TIME_ANALOG = 4
SLEEP_TIME_DISCRETE = 5
FROM_URL = 'http://sensors:8002'
TO_URL_ANALOG = 'http://data-processor-analog:8003/sensors'
TO_URL_DISCRETE = 'http://data-processor-discrete:8004/sensors'


def block_and_wait(url):
    print('Waiting for start TPP')
    while 1:
        try:
            requests.get(url)
            print('TPP is not running. Try again in 5s...')
        except:
            sleep(5)
        finally:
            return
    print('Done!\n')


def sensor_pinger_analog():
    block_and_wait(TO_URL_ANALOG)

    while True:
        try:
            response = requests.get(f'{FROM_URL}/check/analog')
            sensors = response.json()
            response = requests.post(TO_URL_ANALOG, json={'sensors': sensors})
        except Exception as e:
            print('Error to send data to', TO_URL_ANALOG, e)
            block_and_wait(TO_URL_ANALOG)
            
        print('Analog data has been sent to', TO_URL_ANALOG)
        sleep(SLEEP_TIME_ANALOG)


def sensor_pinger_discrete():
    block_and_wait(TO_URL_DISCRETE)

    while True:
        try:
            response = requests.get(f'{FROM_URL}/check/discrete')
            sensors = response.json()
            response = requests.post(TO_URL_DISCRETE, json={'sensors': sensors})
        except Exception as e:
            print('Error to send data to', TO_URL_DISCRETE, e)
            block_and_wait(TO_URL_DISCRETE)

        print('Discrete data has been sent to', TO_URL_DISCRETE)
        sleep(SLEEP_TIME_DISCRETE)


def main():
    print(f'[DEBUG] {MODULE_NAME} started...')
    while 1:
        try:
            requests.get('http://turbine:8001/start')
            break
        except:
            continue            

    print('Running sensor_pinger_analog...')
    thread = Thread(target = sensor_pinger_analog).start()
    print('Running sensor_pinger_discrete...')
    thread = Thread(target = sensor_pinger_discrete).start()
    print(f'Running {MODULE_NAME}_api...')
    start_web()
