import os
import json
import random

from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException


HOST = '0.0.0.0'
PORT = 8002
MODULE_NAME = os.getenv('MODULE_NAME')


app = Flask(__name__)
with open('/module/data/sensors.json', 'r') as file:
    sensors = json.load(file)
turbine_status = 1
turbine_sensor_value = 1


# Заглушка отправки уведомления об изменении состояния турбины
def get_ok_message(status):
    return jsonify({
        'message': f'turbine is {status}',
        'code': 200
    }), 200


# Проверка аналоговых датчиков
@app.route('/check/analog', methods=['GET'])
def check_analog():
    global turbine_status
    global turbine_sensor_value

    process_status = 'running' if turbine_status else 'stopped'

    # Готовим данные датчиков
    sensors_data = []
    for sensor in sensors:
        new_sensor_data = {
            'name': sensor['name'],
            'value': random.randint(sensor['min'], sensor['max']) + random.random(),
            'is_turbine': sensor['is_turbine']
        }
        # Если датчик - трубины
        if sensor['is_turbine']:
            # Нужно убедиться, что он не будет отправляться, если турбина off
            new_sensor_data['value'] *= turbine_status

        sensors_data.append(new_sensor_data)

    return jsonify({
        'sensors': sensors_data,
        'turbine_status': process_status
    }), 200


# Проверка дискретных датчиков
@app.route('/check/discrete', methods=['GET'])
def check_discrete():
    # Переключатель 0 и 1
    global turbine_status
    global turbine_sensor_value
    turbine_sensor_value ^= 1

    # Дискретный датчик
    return jsonify({
        'name': 'sensor_turbine_value',
        'value': turbine_sensor_value * turbine_status
    }), 200


# Установить стату турбины в 1
@app.route('/turbine/start', methods=['GET'])
def turbine_status_start():
    global turbine_status
    turbine_status = 1
    print(1)
    return get_ok_message('running')


# Установить стату турбины в 0
@app.route('/turbine/stop', methods=['GET'])
def turbine_status_stop():
    global turbine_status
    turbine_status = 0
    print(turbine_status)
    return get_ok_message('stopped')


@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({
        "status": e.code,
        "name": e.name,
    }), e.code


def start_web():
    app.run(host=HOST, port=PORT, debug=True, use_reloader=False)
