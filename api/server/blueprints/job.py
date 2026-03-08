from typing import cast
from flask import Blueprint, request, current_app, after_this_request
from ..datatype import MyFlaskApp
from ..websocket.job.namespace import get_job_room, get_task_room
from ..websocket.job.manager import get_unique_job_id

job_bp = Blueprint('job', __name__)

    
def get_app():
    return cast(MyFlaskApp, current_app)

@job_bp.route('/', methods=['POST'])
def create_job():
    """
    Handle the creation of a job based on the provided YouTube link or file.
    """
    app = get_app()
    manager = app.jobManager

    if 'youtubeLink' in request.form:
        youtube_link = request.form['youtubeLink']
        jid, job = manager.create_youtube_job_request(youtube_link)
        
        return {
            "jid": jid
        }
    elif 'file' in request.files:        
        return 'Not implemented yet.', 501
    else:
        return 'No YouTube link or file provided.', 400

def sync_job(app: MyFlaskApp, job_id: str):
    dag_id, dag_run_id = job_id.split('|')
    manager = app.jobManager
    socketio = app.socketio

    dag_run = manager.get_dag_run(dag_id, dag_run_id)
    app.logger.debug(f'Emitting {dag_run}')
    for room in [get_job_room(job_id), get_job_room('*')]:
        socketio.emit('update_job', dag_run, namespace='/job', room=room) # type: ignore

def sync_tasks(app: MyFlaskApp, job_id: str):
    dag_id, dag_run_id = job_id.split('|')
    manager = app.jobManager
    socketio = app.socketio

    task_instances = manager.get_task_instances(dag_id, dag_run_id)
    for task_instance in task_instances:
        app.logger.debug(f'Emitting {task_instance}')
        for room in [get_task_room(job_id), get_task_room('*')]:
            socketio.emit('update_task', task_instance, namespace='/job', room=room) # type: ignore

def sync_task(app: MyFlaskApp, job_id: str, task_id: str, new_status: str):
    dag_id, dag_run_id = job_id.split('|')
    manager = app.jobManager
    socketio = app.socketio

    task_instance = manager.get_task_instance(dag_id, dag_run_id, task_id)
    task_instance['status'] = new_status
    app.logger.debug(f'Emitting {task_instance}')
    for room in [get_task_room(job_id), get_task_room('*')]:
        socketio.emit('update_task', task_instance, namespace='/job', room=room) # type: ignore

@job_bp.route('/<job_id>', methods=['POST'])
def update_job(job_id: str):
    """
    Handle the action to a job based on the job ID.
    """
    app = get_app()
    manager = app.jobManager

    action = request.form.get('action')
    dag_id, dag_run_id = job_id.split('|')
    
    if action == "stop":
        manager.stop_job(dag_id, dag_run_id)
    elif action == "resume":
        manager.restart_job(dag_id, dag_run_id, only_failed=True)
    elif action == "restart":
        manager.restart_job(dag_id, dag_run_id, only_failed=False)

    sync_job(app, job_id)
    sync_tasks(app, job_id)
    return 'ok'

@job_bp.route('/<job_id>/<task_id>/logs', methods=['GET'])
def get_task_log(job_id: str, task_id: str):
    """
    Handle the action to a job based on the job ID.
    """
    app = get_app()
    manager = app.jobManager

    dag_id, dag_run_id = job_id.split('|')
    token = request.args.get('token', default=None)
    task_log = manager.get_task_log(dag_id, dag_run_id, task_id, token)
    return task_log

@job_bp.route('/webhook', methods=['POST'])
def job_webhook() -> tuple:
    """
    Handle job webhook from airflow
    """
    app = get_app()
    
    manager = app.jobManager
    
    data = request.json
    if not data:
        return "No data received", 400

    dag_id = data.get("dag_id")
    dag_run_id = data.get("dag_run_id")
    task_id = data.get("task_id")
    state = data.get("state")

    if not all([dag_id, dag_run_id, task_id, state]):
        return "Missing requied fields", 400
    
    job_id = get_unique_job_id({
        "dag_id": dag_id,
        "dag_run_id": dag_run_id
    })
    
    if task_id == 'DAG':
        sync_job(app, job_id)
        sync_tasks(app, job_id)
    else:
        sync_task(app, job_id, task_id, state)
        sync_job(app, job_id)
    
    return "ok", 200