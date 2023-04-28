import os
import threading
import multiprocessing

from uuid import uuid4
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException


HOST = '0.0.0.0'
PORT = 8006
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
        app_license = user_request.get('app_license')
    except:
        return None

    if not all((user_login, user_password ,user_license)):
        return None

    return {'login': user_login, 'password': user_password,
            'license': user_license, 'app_license': app_license}


# Получение подписи файла
@app.route('/license', methods=['POST'])
def check_sensors():
    user_creds = get_creds(request)
    if not user_creds:
        abort(400)
    
    # Готовим запрос
    req_id = uuid4().__str__()
    details_to_send = {
        'id': req_id,
        'operation': 'update_app',
        'deliver_to': 'update-manager',
        'login': user_creds['login'],
        'password': user_creds['password'],
        'license': user_creds['license'],
        'app_license': user_creds['app_license'],
        'source': 'app-receiver',
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
