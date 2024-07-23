import os
from flask import Flask
from tasks import long_running_task

app = Flask(__name__)

@app.route('/')
def hello():
    result = long_running_task.delay(4, 4)
    return f"Task submitted with id {result.id}"

if __name__ == '__main__':
    app.run(debug=True)