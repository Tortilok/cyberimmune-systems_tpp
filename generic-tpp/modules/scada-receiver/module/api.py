import os
import threading
import multiprocessing

from uuid import uuid4
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException


HOST = '0.0.0.0'
PORT = 8005
MODULE_NAME = os.getenv('MODULE_NAME')

_requests_queue: multiprocessing.Queue = None
app = Flask(__name__)


# Проверяем, что пользователь имеет креды
def get_creds(request) -> dict:
    try:
        user_request = request.json
        user_login = user_request.get('login')
        user_password = user_request.get('password')
        user_license = user_request.get('license')
    except:
        return None

    if not all((user_login, user_password ,user_license)):
        return None

    return {'login': user_login, 'password': user_password,
            'license': user_license}


# Данные от сенсоров
@app.route('/sensors', methods=['POST'])
def check_sensors():
    user_creds = get_creds(request)
    if not user_creds:
        abort(400)
    
    # Готовим запрос
    req_id = uuid4().__str__()
    details_to_send = {
        'id': req_id,
        'operation': 'check_sensors',
        'deliver_to': 'task-scheduler',
        'login': user_creds['login'],
        'password': user_creds['password'],
        'license': user_creds['license'],
        'source': 'scada-receiver',
        'authorized': False
    }

    try:
        _requests_queue.put(details_to_send)
        print(f'{MODULE_NAME} update event: {details_to_send}')
    except:
        abort(400)
    
    return jsonify({'message': 'Ok', 'status': 200}), 200


# Изменение настроек
@app.route('/settings', methods=['POST'])
def update_settings():
    user_creds = get_creds(request)
    if not user_creds:
        abort(400)

    new_settings = request.json.get('settings')
    if not new_settings:
        abort(400)

    # Готовим запрос
    req_id = uuid4().__str__()
    details_to_send = {
        'id': req_id,
        'operation': 'update_settings',
        'deliver_to': 'task-scheduler',
        'login': user_creds['login'],
        'password': user_creds['password'],
        'license': user_creds['license'],
        'settings': new_settings,
        'source': 'scada-receiver',
        'authorized': False
    }

    try:
        _requests_queue.put(details_to_send)
        print(f'{MODULE_NAME} update event: {details_to_send}')
    except:
        abort(400)
    
    return jsonify({'message': 'Ok', 'status': 200}), 200    


@app.route('/turbine/stop', methods=['POST'])
def turbine_stop():
    user_creds = get_creds(request)
    if not user_creds:
        abort(400)
    
    # Готовим запрос
    req_id = uuid4().__str__()
    details_to_send = {
        'id': req_id,
        'operation': 'turbine_stop',
        'deliver_to': 'task-scheduler',
        'login': user_creds['login'],
        'password': user_creds['password'],
        'license': user_creds['license'],
        'source': 'scada-receiver',
        'authorized': False
    }

    try:
        _requests_queue.put(details_to_send)
        print(f'{MODULE_NAME} update event: {details_to_send}')
    except:
        abort(400)
    
    return jsonify({'message': 'Ok', 'status': 200}), 200


@app.route('/turbine/start', methods=['POST'])
def turbine_start():
    user_creds = get_creds(request)
    if not user_creds:
        abort(400)
    
    # Готовим запрос
    req_id = uuid4().__str__()
    details_to_send = {
        'id': req_id,
        'operation': 'turbine_start',
        'deliver_to': 'task-scheduler',
        'login': user_creds['login'],
        'password': user_creds['password'],
        'license': user_creds['license'],
        'source': 'scada-receiver',
        'authorized': False
    }

    try:
        _requests_queue.put(details_to_send)
        print(f'{MODULE_NAME} update event: {details_to_send}')
    except:
        abort(400)
    
    return jsonify({'message': 'Ok', 'status': 200}), 200


@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({
        "status": e.code,
        "name": e.name,
    }), e.code


def start_web(requests_queue):
    global _requests_queue

    _requests_queue = requests_queue

    threading.Thread(target=lambda: app.run(
        host=HOST, port=PORT, debug=True, use_reloader=False
    )).start()
