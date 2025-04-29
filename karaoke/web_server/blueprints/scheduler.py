import os

from flask import Blueprint, request, g, send_file
from ..scheduler import SchedulerBinder
from ...utils.config import get_logger, Config

scheduler_bp = Blueprint('scheduler', __name__)
config = Config()
logger = get_logger(__name__, config.log_level)

@scheduler_bp.before_request
def prepare_binder() -> None:
    """
    Prepare the binder for the request marked with _require_binder.
    This is called before each request to ensure that the scheduler is bound.
    """
    scheduler = SchedulerBinder()
    try:
        scheduler.bind()
    except Exception as e:
        logger.error(f"Failed to bind scheduler: {e}")
        return {
            'success': False,
            'message': 'Scheduler is not connected'
        }, 500
    g.scheduler = scheduler

@scheduler_bp.teardown_request
def close_binder(exception: Exception) -> None:
    """
    Close the binder after the request is completed.
    This is called after each request to ensure that the scheduler is closed.
    """
    scheduler: SchedulerBinder = getattr(g, 'scheduler', None)
    scheduler.close()

@scheduler_bp.route('/create-job', methods=['POST'])
def create_job() -> tuple:
    """
    Handle the creation of a job based on the provided YouTube link or file.
    """
    scheduler: SchedulerBinder = g.scheduler
    if 'youtubeLink' in request.form:
        youtube_link = request.form['youtubeLink']
        logger.info(f"Processing YouTube link: {youtube_link}")
        return scheduler.create_by_YT(youtube_link)
    elif 'file' in request.files:        
        return 'File upload is not supported yet.', 501
    else:
        return 'No YouTube link or file provided.', 400

@scheduler_bp.route('/artifact/<job_id>/<artifact_type>/<int:artifact_index>', methods=['GET'])
def get_artifact(job_id: str, artifact_type: str, artifact_index: int) -> tuple:
    """
    Handle the retrieval of artifacts based on the job ID and artifact index.
    """
    scheduler: SchedulerBinder = g.scheduler
    result = scheduler.get_artifact(job_id, artifact_type, artifact_index)
    if artifact_type == 'file':
        path = os.path.join(config.media_path, result)
        return send_file(path)
    else:
        return result
