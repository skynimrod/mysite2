from celery import Celery

app = Celery('tasks', broker='amqp://guest@localhost//')

@app.task
def add(x,y):
    print('add(x,y)')
    return x+y

#@periodic_task( run_every=(crontab(minute='*/15')),name='adams_add',ignore_result=True )
def addp(x,y):
    print('periodic add:x,y')
    return x+y
