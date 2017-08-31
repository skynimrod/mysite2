from celery import Celery

import time

app = Celery('report_tasks', broker='amqp://quest@localhost//')
@app.task

def hello():
    t = time.now()
    print(t)
    return 'hello world'
