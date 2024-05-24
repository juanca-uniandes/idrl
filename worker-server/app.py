import base64
import json
import os
import uuid
import time
from flask import Flask, request, jsonify
import logging
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler
import multiprocessing

from tasks import process_video
from util import fn_info_task

# Configuración de Google Cloud Logging
client = google.cloud.logging.Client()
handler = CloudLoggingHandler(client)
cloud_logger = logging.getLogger('cloudLogger')
cloud_logger.setLevel(logging.INFO)
cloud_logger.addHandler(handler)

app = Flask(__name__)
tasks = {}
ALLOWED_EXTENSIONS = {'mp4'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def OK():
    return 'BASE OK OK OK!'

@app.route('/tasks', methods=['POST'])
def pubsub_handler():
    envelope = request.get_json()
    if not envelope:
        cloud_logger.error('No Pub/Sub message received')
        return 'Bad Request: no Pub/Sub message received', 400

    pubsub_message = envelope.get('message')

    if not pubsub_message:
        cloud_logger.error('Invalid Pub/Sub message format')
        return 'Bad Request: invalid Pub/Sub message format', 400

    message_data = pubsub_message.get('data')

    if message_data:
        try:
            decoded_bytes = base64.decodebytes(message_data.encode('utf-8'))
            decoded_str = decoded_bytes.decode('utf-8')
            url = json.loads(decoded_str)["url"]
            cloud_logger.info("Envelope received", extra={
                "labels": {
                    "envelope": json.dumps(envelope),
                    "message": json.dumps(pubsub_message),
                    "message_data": message_data,
                    "url": url
                }},
            )            
            task_id = str(uuid.uuid4().int)[:18]
            current_user = 1

            # Iniciando el proceso de forma asíncrona usando multiprocessing
            process = multiprocessing.Process(target=process_video, args=(task_id, url, current_user))
            process.start()
            tasks[task_id] = process
            process.join(timeout=300)  # Espera un máximo de 5 minutos
            return jsonify(message=f'Task {task_id} started'), 200

        except Exception as e:
            cloud_logger.error(f'Error decoding message: {e}')
            return 'Bad Request: error decoding message', 400
    else:
        cloud_logger.info('Received empty message')

    return 'OK', 200

@app.route('/tasks/<task_id>', methods=['DELETE'])
def cancel_task(task_id):
              
        result = fn_info_task(task_id)
        if not result:
            return jsonify(error=f'Error al cancelar la tarea: Tarea {task_id} no encontrada'), 404

        task_info = {'task_id': result[0][0], 'status': result[0][1], 'url': result[0][2]}

        # Validar el estado de la tarea
        if task_info['status'] != 'Procesado':
            time.sleep(60)
            result = fn_info_task(task_id)
            if not result:
                return jsonify(error=f'Error al cancelar la tarea: Tarea {task_id} no encontrada'), 404

            return jsonify(message=f'Tarea {task_id} en estado Procesado, se eliminará el registro'), 200
        
        if task_info['status'] == 'Procesado':
            return jsonify(message=f'Tarea {task_id} en estado Procesado, se eliminará el registro'), 200

        if task_id in tasks:
            process = tasks[task_id]
            if process.is_alive():
                process.terminate()

                process.join()  # Espera a que el proceso termine
                del tasks[task_id]
                return jsonify(message=f'Tarea {task_id} cancelada'), 200
            else:
                del tasks[task_id]
                return jsonify(message=f'Tarea {task_id} ya terminada'), 200
        else:
            return jsonify(message=f'Tarea {task_id} no encontrada'), 404

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
