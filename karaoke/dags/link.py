import requests

from enum import Enum
from datetime import datetime
from airflow.sdk import DAG, Param
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.http.notifications.http import send_http_notification

class QueueType(Enum):
    BASE = "base_tasks_queue"
    GPU = "gpu_tasks_queue"

def report_state_to_server():
    return send_http_notification(
        http_conn_id="job_webhook_server",
        endpoint="api/job/webhook",
        method="POST",
        json={
            "dag_id": "{{ dag.dag_id }}",
            "dag_run_id": "{{ run_id }}",
            "task_id": "{{ task_instance.task_id }}",
            "state": "{{ task_instance.state.value }}"
        },
    )

def report_state_to_server_callback(context):
    sender = send_http_notification(
        http_conn_id="job_webhook_server",
        endpoint="api/job/webhook",
        method="POST",
        json={
            "dag_id": "{{ dag.dag_id }}",
            "dag_run_id": "{{ run_id }}",
            "task_id": "{{ 'DAG' }}",
            "state": "{{ dag_run.state }}"
        },
    )
    sender(context)

with DAG(
    "Generate-from-link",
    params={
        "request_file_id": Param("", type="string", description="File id in storage"),
    },
    description="Download video from a link and generate karaoke version.",
    schedule=None, 
    start_date=datetime(2026, 1, 1),
    catchup=False,
    on_success_callback=report_state_to_server_callback,
    on_failure_callback=report_state_to_server_callback,
    default_args={
        "on_execute_callback": report_state_to_server(),
        "on_failure_callback": report_state_to_server(),
        "on_success_callback": report_state_to_server()
    },
    tags=[]
) as dag:
    exec_prefix = "PYTHONPATH=/opt/airflow/dags python -m tasks"
    mm_exec_prefix = "PYTHONPATH=/opt/airflow/dags /opt/env/bin/python -m tasks"
    download_audio = BashOperator(
        task_id="download_audio",
        task_display_name="Audio Downloading",
        bash_command=f"{exec_prefix}.download cloud --run_id '{{{{ run_id }}}}' --type audio --file_id '{{{{ params.request_file_id }}}}'",
        do_xcom_push=True,
        queue=QueueType.BASE.value
    )

    identify = BashOperator(
        task_id="identify_audio",
        task_display_name="Music identification",
        bash_command=f"{exec_prefix}.identify cloud --run_id '{{{{ run_id }}}}' --file_id '{{{{ ti.xcom_pull(task_ids='download_audio') }}}}'",
        do_xcom_push=True,
        queue=QueueType.BASE.value
    )

    lyrics = BashOperator(
        task_id="retrive_lyrics",
        task_display_name="Lyrics retrieval",
        bash_command=f"""{exec_prefix}.lyric cloud --run_id '{{{{ run_id }}}}' \
            --file_ids '{{{{ ti.xcom_pull(task_ids='download_audio') }}}}' \
                '{{{{ ti.xcom_pull(task_ids='identify_audio') }}}}' 
        """,
        do_xcom_push=True,
        queue=QueueType.BASE.value
    )

    separate = BashOperator(
        task_id="voice_separation",
        task_display_name="Vocal Separation",
        bash_command=f"{exec_prefix}.separate cloud --run_id '{{{{ run_id }}}}' --file_id '{{{{ ti.xcom_pull(task_ids='download_audio') }}}}'",                
        do_xcom_push=True,
        queue=QueueType.GPU.value
    )
    
    vad = BashOperator(
        task_id="voice_detection",
        task_display_name="Voice activity detection",
        bash_command=f"{exec_prefix}.detect cloud --run_id '{{{{ run_id }}}}' --file_id '{{{{ ti.xcom_pull(task_ids='voice_separation') }}}}'",
        do_xcom_push=True,
        queue=QueueType.BASE.value
    )

    transcript = BashOperator(
        task_id="voice_transcription",
        task_display_name="Lyrics Transcription",
        bash_command=f"""{exec_prefix}.transcript cloud --run_id '{{{{ run_id }}}}' \
            --file_ids '{{{{ ti.xcom_pull(task_ids='voice_separation') }}}}' \
             '{{{{ ti.xcom_pull(task_ids='voice_detection') }}}}' \
             '{{{{ ti.xcom_pull(task_ids='retrive_lyrics') }}}}' \
        """,                
        do_xcom_push=True,
        queue=QueueType.GPU.value
    )

    mapping = BashOperator(
        task_id="lyrics_mapping",
        task_display_name="Merge transcription and lyrics",
        bash_command=f"""{exec_prefix}.mapping cloud --run_id '{{{{ run_id }}}}' \
            --file_ids '{{{{ ti.xcom_pull(task_ids='voice_transcription') }}}}' \
             '{{{{ ti.xcom_pull(task_ids='retrive_lyrics') }}}}' \
        """,                
        do_xcom_push=True,
        queue=QueueType.BASE.value
    )

    sentence = BashOperator(
        task_id="generate_sentence",
        task_display_name="Generate Sentence",
        bash_command=f"""{exec_prefix}.sentence cloud --run_id '{{{{ run_id }}}}' \
            --file_ids '{{{{ ti.xcom_pull(task_ids='lyrics_mapping') }}}}'
        """,                
        do_xcom_push=True,
        queue=QueueType.BASE.value
    )

    subtitle = BashOperator(
        task_id="generate_subtitle",
        task_display_name="Subtitle Generation",
        bash_command=f"""{exec_prefix}.subtitle cloud --run_id '{{{{ run_id }}}}' \
            --file_ids '{{{{ ti.xcom_pull(task_ids='generate_sentence') }}}}' \
            '{{{{ ti.xcom_pull(task_ids='download_audio') }}}}' \
            '{{{{ ti.xcom_pull(task_ids='identify_audio') }}}}'
        """,                
        do_xcom_push=True,
        queue=QueueType.BASE.value
    )
    
    [download_audio, sentence] >> subtitle
    [separate, mapping] >> sentence
    [transcript, lyrics] >> mapping
    [separate, vad, lyrics] >> transcript
    separate >> vad
    [download_audio, identify] >> lyrics
    download_audio >> identify
    download_audio >> separate
