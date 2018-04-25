# worker.py
"""Worker functionality, designed to listen to a ongoing queue and process queued tasks"""

import os
import redis
from rq import Worker, Queue, Connection


__version__ = '0.1'
__author__ = 'RoViT (KU)'

listen = ['default']

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)
print('WORKER STARTED, reids SERVER STARTED, RUNNING ON PID: {}'.format(conn.connection_pool.pid))

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
