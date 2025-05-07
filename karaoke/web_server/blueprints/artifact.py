import os

from flask import Blueprint, request, g, send_file
from ..scheduler import SchedulerBinder
from ...utils.task import ArtifactType
from ...utils.config import get_logger, Config

artifact_bp = Blueprint('artifact', __name__)
config = Config()
logger = get_logger(__name__, config.log_level)

@artifact_bp.before_request
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
        return 'Scheduler is not connected', 500
    g.scheduler = scheduler

@artifact_bp.teardown_request
def close_binder(exception: Exception) -> None:
    """
    Close the binder after the request is completed.
    This is called after each request to ensure that the scheduler is closed.
    """
    scheduler: SchedulerBinder = getattr(g, 'scheduler', None)
    if scheduler:        
        scheduler.close()
@artifact_bp.route('/artifact/<job_id>/<int:artifact_index>', methods=['GET'])
def get_artifact(job_id: str, artifact_index: int) -> tuple:
    """
    Handle the retrieval of artifacts based on the job ID and artifact index.
    """
    scheduler: SchedulerBinder = g.scheduler
    result = scheduler.get_artifact(job_id, artifact_index)
    artifact_type = ArtifactType(result['artifact_type'])
    artifact = result['artifact']
    if artifact_type in [ArtifactType.VIDEO, ArtifactType.AUDIO]:
        path = os.path.join(config.media_path, artifact)
        return send_file(path)
    else:
        return artifact
