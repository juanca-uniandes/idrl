# tasks.py
from celery import Celery
import time

broker_url = 'redis://redis:6379/0'
app = Celery('tasks', backend='rpc://', broker=broker_url)
 
@app.task(bind=True)
def process_video(self, url):
    for i in range(1, 6):
        time.sleep(5)
        self.update_state(state='PROGRESS', meta={'progress': i*20})
    return {'status': 'completado!', 'result': 42}