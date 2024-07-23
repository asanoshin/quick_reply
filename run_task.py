import os
from flask import Flask, jsonify
from tasks import long_running_task, app as celery_app

app = Flask(__name__)

@app.route('/')
def hello():
    result = long_running_task.delay(4, 5)
    return f"Task submitted with id {result.id}"


@app.route('/status/<task_id>')
def get_status(task_id):
    result = celery_app.AsyncResult(task_id)
    if result.state == 'PENDING':
        response = {
            'task_id': task_id,
            'task_status': 'Pending...',
            'task_result': None
        }
    elif result.state == 'SUCCESS':
        response = {
            'task_id': task_id,
            'task_status': 'Completed',
            'task_result': result.result
        }
    elif result.state == 'FAILURE':
        response = {
            'task_id': task_id,
            'task_status': 'Failed',
            'task_result': str(result.result)  # Error message
        }
    else:
        response = {
            'task_id': task_id,
            'task_status': 'In Progress...',
            'task_result': None
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)