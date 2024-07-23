from celery import Celery
import time

# 假設您的 Redis URL
redis_url = "rediss://:pac2484ffa244b6dbed12e3e37b44090ce54d8e6685ac09a89825acd0980d4081@ec2-3-218-138-147.compute-1.amazonaws.com:17669"

# 創建 Celery 應用
app = Celery('tasks', broker=redis_url, backend=redis_url)

# 配置 Celery
app.conf.update(
    broker_use_ssl={
        'ssl_cert_reqs': None  # 禁用證書驗證
    },
    redis_backend_use_ssl={
        'ssl_cert_reqs': None  # 禁用證書驗證
    }
)

@app.task
def long_running_task(x, y):
    time.sleep(5)
    result = x + y
    print(f"Task completed with result {result}")
    return result

if __name__ == '__main__':
    print("Starting Celery worker...")
    app.start()
