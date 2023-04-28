import os
import requests

from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException


HOST = '0.0.0.0'
PORT = 8001
MODULE_NAME = os.getenv('MODULE_NAME')


app = Flask(__name__)
turbine_status = 1


# Проверка состояния
@app.route('/check', methods=['GET'])
def check():
    global turbine_status
    process_status = 'running' if turbine_status else 'stopped'

    return jsonify({
        'message': f'turbine is {process_status}',
        'turbine_status': turbine_status
    }), 200


# Запуск турбины
@app.route('/start', methods=['GET'])
def start():
    global turbine_status
    turbine_status = 1
    
    response = requests.get('http://sensors:8002/turbine/start')
    if response.status_code != 200:
        abort(400)

    return check()


# Остановка турбины
@app.route('/stop', methods=['GET'])
def stop():
    global turbine_status
    turbine_status = 0

    response = requests.get('http://sensors:8002/turbine/stop')
    if response.status_code != 200:
        abort(400)

    return check()


@app.errorhandler(HTTPException)
def handle_exception(e):
    return jsonify({
        "status": e.code,
        "name": e.name,
    }), e.code


def start_web():
    app.run(host=HOST, port=PORT, debug=True, use_reloader=False)
