from apiflask import APIFlask, abort
from flask import request
from werkzeug.middleware.proxy_fix import ProxyFix
from rq import Queue
from rq.job import Job
from .worker import connection
from .auth import check_netbox_auth
from .tasks import task_enqueue_vlan_create, task_enqueue_vlan_delete
from dynaconf import FlaskDynaconf

# Initialize APIFlask
app = APIFlask(__name__, "Middleware VLAN Deployment", version="1.0", docs_path="/")
app.config['DESCRIPTION'] = "LiveLAB: VLAN deployment on Cisco devices"

FlaskDynaconf(app, env_var_prefix="APP")

# Proxy fix if used behind reverse proxy
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Load config from env variables which prefixed with APP_
app.config.from_prefixed_env(prefix="APP")

q = Queue(connection=connection, name=app.config.QUEUE_NAME)

@app.get("/hello")
def index():
    return {"message": "Hello World", "queue": app.config.QUEUE_NAME}, 200


@app.post("/vlan_webhook")
@check_netbox_auth
def vlan_webhook():
    json = request.json

    if "updated" in json['event'] or "created" in json['event']:
        try:
            vlan_id = json['data']['vid']
            vlan_name = json['data']['name']
            vlan_site = json['data']['site']['slug']

            job = Job.create(
                func=task_enqueue_vlan_create,
                args=(vlan_id, vlan_name, vlan_site), connection=connection
            )

            q.enqueue_job(job)
        except Exception as e:
            print(e)
            return abort(500, message="Failed to create job")

    if "deleted" in json['event']:
        try:
            vlan_id = json['data']['vid']
            vlan_site = json['data']['site']['slug']

            job = Job.create(
                func=task_enqueue_vlan_delete,
                args=(vlan_id, vlan_site), connection=connection
            )

            q.enqueue_job(job)
        except Exception as e:
            print(e)
            return abort(500, message="Failed to create job")

    return {"state": "ok"}
