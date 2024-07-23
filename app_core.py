from flask import Flask, request, jsonify
from tasks import print_squares
from celery.result import AsyncResult

app = Flask(__name__)

@app.route('/print_squares', methods=['POST'])
def trigger_print_squares():
    task = print_squares.delay()
    return jsonify({"task_id": task.id}), 202

@app.route('/result/<task_id>', methods=['GET'])
def get_result(task_id):
    task = AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'result': task.result
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info)
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
