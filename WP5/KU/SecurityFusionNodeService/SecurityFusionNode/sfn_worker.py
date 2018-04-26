# sfn_worker.py
"""Worker functionality, designed to listen to a ongoing queue and process queued tasks"""

import os
import redis
from rq import Worker, Queue, Connection
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).absolute().parents[4]))
sys.path.append(str(Path(__file__).absolute()))


__version__ = '0.1'
__author__ = 'RoViT (KU)'

listen = ['default']

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    print('WORKER STARTED, redis SERVER STARTED, RUNNING ON PID: {}'.format(conn.connection_pool.pid))
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
