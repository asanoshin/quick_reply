from celery import Celery
import time
import ssl

# 假設您的 Redis URL
redis_url = "rediss://:pa602ae39e13e8a7209c611d22c0a03c57884120fd7caef65ef14f53485bd842d@ec2-3-232-151-78.compute-1.amazonaws.com:30539"

# 創建 Celery 應用
app = Celery('tasks', broker=redis_url, backend=redis_url)

# 配置 Celery
app.conf.update(
    broker_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE  # 使用 ssl.CERT_NONE 而不是 None
    },
    redis_backend_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE  # 使用 ssl.CERT_NONE 而不是 None
    },
    broker_connection_retry_on_startup=True
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