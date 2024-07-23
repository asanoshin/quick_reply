import os
from celery import Celery

redis_url = os.environ.get('REDIS_URL', 'rediss://:p2747f965299f0534af9dd1f1c3fbb57cc9ef45a3bdaac6dcf70da1ca1dc45daa@ec2-54-91-164-149.compute-1.amazonaws.com:20070?ssl_cert_reqs=CERT_NONE')
app = Celery('tasks', broker=redis_url, backend=redis_url)

@app.task
def long_running_task(x, y):
    import time
    time.sleep(5)
    return x + y
