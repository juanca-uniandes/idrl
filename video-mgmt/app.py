# app.py
from flask import Flask, request, jsonify
from tasks import app as celery_app, process_video

app = Flask(__name__)

@app.route('/start', methods=['POST'])
def start():
    url = request.json['url']
    task = process_video.delay(url)
    return jsonify({'task_id': str(task.id)}), 202

@app.route('/status/<task_id>', methods=['GET'])
def status(task_id):
    task = celery_app.AsyncResult(task_id)
    return jsonify({'state': str(task.state), 'info': task.info}), 200

@app.route('/abort/<task_id>', methods=['DELETE'])
def abort(task_id):
    task = celery_app.AsyncResult(task_id)
    task.revoke(terminate=True)
    return jsonify({'status': 'Task aborted!'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)