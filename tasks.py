from celery import Celery

# 創建Celery應用
app = Celery('tasks', broker='rediss://:p2747f965299f0534af9dd1f1c3fbb57cc9ef45a3bdaac6dcf70da1ca1dc45daa@ec2-54-91-164-149.compute-1.amazonaws.com:20070?ssl_cert_reqs=CERT_NONE', backend='rediss://:p2747f965299f0534af9dd1f1c3fbb57cc9ef45a3bdaac6dcf70da1ca1dc45daa@ec2-54-91-164-149.compute-1.amazonaws.com:20070?ssl_cert_reqs=CERT_NONE')

# 定義一個耗時的任務
@app.task
def long_running_task(x, y):
    # 模擬一個耗時的操作
    import time
    time.sleep(5)
    return x + y
