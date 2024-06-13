from rq import Worker, Queue, Connection
from vlan_deploy.worker import connection, listen


if __name__ == '__main__':
    with Connection(connection):
        worker = Worker(list(map(Queue, listen)))
        worker.work()