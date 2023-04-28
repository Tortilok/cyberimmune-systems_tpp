import os
import json
import threading
import multiprocessing

from uuid import uuid4
from flask import Flask, request, jsonify, abort
from confluent_kafka import Consumer, OFFSET_BEGINNING
from werkzeug.exceptions import HTTPException


HOST = '0.0.0.0'
PORT = 8004
MODULE_NAME = os.getenv('MODULE_NAME')

_requests_queue: multiprocessing.Queue = None

app = Flask(__name__)


# Данные от сенсоров
@app.route('/sensors', methods=['POST'])
def get_sensors():
    try:
        data_json = request.json
        sensors_data = data_json['sensors']
    except:
        abort(400)

    # Готовим запрос
    req_id = uuid4().__str__()
    details_to_send = {
        'id': req_id,
        'operation': 'store_discrete',
        'deliver_to': 'data-storage',
        'data': sensors_data
    }

    req_id2 = uuid4().__str__()
    details_to_send2 = {
        'id': req_id2,
        'operation': 'store_discrete',
        'deliver_to': 'app',
        'data': sensors_data
    }


    try:
        _requests_queue.put(details_to_send)
        print(f'{MODULE_NAME} update event: {details_to_send}')
        _requests_queue.put(details_to_send2)
        print(f'{MODULE_NAME} update event: {details_to_send2}')
    except:
        abort(400)

    return jsonify({
        'message': 'The data has been sent!',
        'status': 200
    }), 200


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
