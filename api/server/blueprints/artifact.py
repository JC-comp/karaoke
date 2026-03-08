import os
import re
from flask import Blueprint, send_file, current_app, Response, stream_with_context, request
from typing import cast
from ..datatype import MyFlaskApp

artifact_bp = Blueprint('artifact', __name__)

@artifact_bp.route('/<path:artifact_path>', methods=['GET'])
def get_artifact(artifact_path: str):
    """
    Handle the retrieval of artifacts based on the job ID and artifact id from minio.
    """
    app = cast(MyFlaskApp, current_app)
    storage = app.storage

    # Get file size
    try:
        stat = storage.stat_object(artifact_path)
        file_size = stat.size
        if file_size == 0 or file_size is None:
            return {"error": "Artifact not found"}, 404
    except Exception:
        return {"error": "Artifact not found"}, 404

    # Check range header
    range_header = request.headers.get('Range', None)
    byte_start = 0
    byte_end = file_size - 1
    status_code = 200
    if range_header:
        match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if match:
            byte_start = int(match.group(1))
            if match.group(2):
                byte_end = int(match.group(2))
            status_code = 206
    requested_length = byte_end - byte_start + 1

    try:
        response = storage.stream_binary(artifact_path, offset=byte_start, length=requested_length)
        def generate():
            try:
                # Yield chunks of 64KB
                for chunk in response.stream(65536):
                    yield chunk
            finally:
                response.close()
                response.release_conn()

        headers = {
            "Content-Type": response.headers.get("Content-Type", 'application/octet-stream'),
            "Content-Disposition": f"attachment; filename={os.path.basename(artifact_path)}",
            "Accept-Ranges": "bytes",
        }

        if status_code == 206:
            headers["Content-Range"] = f"bytes {byte_start}-{byte_end}/{file_size}"
            headers["Content-Length"] = str(requested_length)
        else:
            headers["Content-Length"] = str(file_size)

        return Response(
            stream_with_context(generate()),
            status=status_code, 
            headers=headers
        )
    except Exception as e:
        current_app.logger.error(f"Failed to fetch artifact {artifact_path}: {e}", exc_info=True)
        return {"error": "Artifact not found"}, 404
    