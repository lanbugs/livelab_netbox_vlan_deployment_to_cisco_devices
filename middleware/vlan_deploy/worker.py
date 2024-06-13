import os
import redis
from rq import Worker, Queue, Connection

# Queues to listen to
listen = [os.getenv('APP_QUEUE_NAME', 'default')]

# URL to redis server
redis_url = os.getenv('APP_REDIS_URL', 'redis://localhost:6379')

# create redis connection
connection = redis.from_url(redis_url)

if __name__ == '__main__':
    # start the worker if directly called
    with Connection(connection):
        worker = Worker(list(map(Queue, listen)))
        worker.work()