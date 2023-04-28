import os
import requests
import threading

from time import sleep
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException


HOST = '0.0.0.0'
PORT = 8000
MODULE_NAME = os.getenv('MODULE_NAME')
app = Flask(__name__)
URL = 'http://scada-receiver:8005'
user_data = {}

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

    global user_data
    user_data[user_login] = {'password': user_password,
                             'license': user_license}

    return {'login': user_login, 'password': user_password,
            'license': user_license}


# Данные от сенсоров
@app.route('/sensors', methods=['POST'])
def check_sensors():
    user_creds = get_creds(request)
    if not user_creds:
        abort(400)
    
    # Готовим запрос
    response = requests.post(f'{URL}/sensors', json=user_creds)
    if response.status_code != 200:
        abort(400)

    global user_data
    if not user_data.get(user_creds['login']):
        abort(400)

    for _ in range(220):
        user = user_data[user_creds['login']]
        if not user.get('details'):
            sleep(0.5)
            continue
        details = user['details']
        return jsonify(details), details['status']

    abort(400)


# Данные от сенсоров
@app.route('/update', methods=['POST'])
def update():
    user_creds = get_creds(request)
    if not user_creds:
        abort(400)
    
    app_license = request.json.get('app_license')
    if not app_license:
        abort(400)

    user_creds['app_license'] = app_license

    # Готовим запрос
    response = requests.post(f'http://app-receiver:8006/license', json=user_creds)
    if response.status_code != 200:
        abort(400)

    global user_data
    if not user_data.get(user_creds['login']):
        abort(400)

    for _ in range(220):
        user = user_data[user_creds['login']]
        if not user.get('details'):
            sleep(0.5)
            continue
        details = user['details']
        return jsonify(details), details['status']

    abort(400)


# Изменение настроек
@app.route('/settings', methods=['POST'])
def update_settings():
    user_creds = get_creds(request)
    if not user_creds:
        abort(400)

    new_settings = request.json.get('settings')
    if not new_settings:
        abort(400)
    
    user_creds['settings'] = new_settings

    # Готовим запрос
    response = requests.post(f'{URL}/settings', json=user_creds)
    if response.status_code != 200:
        abort(400)

    global user_data
    if not user_data.get(user_creds['login']):
        abort(400)

    for _ in range(20):
        user = user_data[user_creds['login']]
        if not user.get('details'):
            sleep(0.5)
            continue
        details = user['details']
        return jsonify(details), details['status']

    abort(400)


@app.route('/turbine/stop', methods=['POST'])
def turbine_stop():
    user_creds = get_creds(request)
    if not user_creds:
        abort(400)
    
    # Готовим запрос
    response = requests.post(f'{URL}/turbine/stop', json=user_creds)
    if response.status_code != 200:
        abort(400)

    global user_data
    if not user_data.get(user_creds['login']):
        abort(400)

    for _ in range(20):
        user = user_data[user_creds['login']]
        if not user.get('details'):
            sleep(0.5)
            continue
        details = user['details']
        return jsonify(details), details['status']

    abort(400)


@app.route('/turbine/start', methods=['POST'])
def turbine_start():
    user_creds = get_creds(request)
    if not user_creds:
        abort(400)
    
    # Готовим запрос
    response = requests.post(f'{URL}/turbine/start', json=user_creds)
    if response.status_code != 200:
        abort(400)

    global user_data
    if not user_data.get(user_creds['login']):
        abort(400)

    for _ in range(20):
        user = user_data[user_creds['login']]
        if not user.get('details'):
            sleep(0.5)
            continue
        details = user['details']
        return jsonify(details), details['status']

    abort(400)


@app.route('/send_data', methods=['POST'])
def send_message():
    try:
        user_request = request.json
        login = user_request['login']
        password_hash = user_request['password']
        user_license = user_request['license']
        details = user_request['details']
    except:
        abort(400)
    
    global messages
    if not user_data.get(login):
        abort(403)

    user = user_data[login]
    if not all((user['password'] == password_hash,
                user['license'] == user_license)):
        abort(403)
    user_data[login]['details'] = details
    return jsonify({'message': 'ok!', 'status': 200})


@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    return jsonify({
        "status": e.code,
        "name": e.name,
    }), e.code


def start_web():
    threading.Thread(target=lambda: app.run(
        host=HOST, port=PORT, debug=True, use_reloader=False
    )).start()
