import json
import os
import uuid

from typing import Generator
from redis import Redis
from ...airflow import AirflowManager, Storage, BucketType
from ...config import config

def get_unique_job_id(dag_run: dict) -> str:
    return f"{dag_run.get('dag_id')}|{dag_run.get('dag_run_id')}"

def parse_dag_run(dag_run: dict):
    return {
        "jid": get_unique_job_id(dag_run),
        "created_at": dag_run.get('logical_date'),
        "started_at": dag_run.get('start_date'),
        "finished_at": dag_run.get('end_date'),
        "status": dag_run.get("state")
    }

def parse_task_order(tasks: list[dict]) -> list[str]:
    dependencies = {}
    in_degree = {t['task_id']: 0 for t in tasks}
    
    for t in tasks:
        task_id = t['task_id']
        downstreams = t.get('downstream_task_ids', [])
        dependencies[task_id] = downstreams
        for down in downstreams:
            in_degree[down] += 1

    queue = [t for t, degree in in_degree.items() if degree == 0]
    ordered_list = []

    while queue:
        current = queue.pop(0)
        ordered_list.append(current)
        for neighbor in dependencies.get(current, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return ordered_list

def parse_task_instance(task_instance: dict):
    return {
        "jid": get_unique_job_id(task_instance),
        "tid": task_instance.get("task_id"),
        "name": task_instance.get("task_display_name"),
        "status": task_instance.get("state")
    }

class JobManager:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.cache_ttl = 3600 # 1 hour
        self.storage = Storage()
        self.airflow_manager = AirflowManager(
            config.airflow.base_url,
            (config.airflow.username, config.airflow.password)
        )

    def create_youtube_job_request(self, youtube_link: str) -> tuple[str, dict]:
        """
        Writes a JSON request to MinIO and returns the object path.
        """
        request_id = uuid.uuid4().hex
        file_path = f"request/{request_id}.json"

        content = {
            "results": {
                "url": {
                    "value": youtube_link,
                }
            },
            "artifact_keys":[],
            "exports":[]
        }
        json_data = json.dumps(content).encode('utf-8')
        result = self.storage.put_binary(
            BucketType.ARG_BUCKET, file_path, json_data, content_type='application/json'
        )
        request_file_id = os.path.join(result.bucket_name, result.object_name)
        job = self.airflow_manager.trigger_airflow_job(config.airflow.dag_id, request_file_id)
        return (
            get_unique_job_id(job),
            job
        )

    def stop_job(self, dag_id: str, dag_run_id: str):
        self.airflow_manager.patch_dag_run(dag_id, dag_run_id, state='failed')

    def restart_job(self, dag_id: str, dag_run_id: str, only_failed: bool):
        if only_failed:
            task_instances = self.airflow_manager.get_task_instances(dag_id, dag_run_id)
            failed_task_ids = [task_instance.get('task_id') for task_instance in task_instances if task_instance.get('state') != 'success']
            if failed_task_ids:
                self.airflow_manager.clear_task_instances(dag_id, dag_run_id, failed_task_ids=failed_task_ids)
        else:
            self.airflow_manager.clear_task_instances(dag_id, dag_run_id, failed_task_ids=None)

    def get_dag_ids(self, use_cache=True) -> list[str]:
        dags = self.airflow_manager.get_dags()
        dag_ids = [dag.get('dag_id') for dag in dags]
        return dag_ids
    
    def get_dag_run_source(self, request_file_id: str, use_cache=True):
        data = self.storage.read_json(request_file_id)
        return data.get('results')

    def get_task_export(self, dag_id: str, dag_run_id: str, task_id: str) -> dict:
        task_export = {}
        filepath = self.airflow_manager.get_task_result_filepath(dag_id, dag_run_id, task_id)
        if not filepath:
            return task_export
        try:
            args = self.storage.read_json(filepath)
            artifact_keys = args.get('artifact_keys')
            results = args.get('results')
            exports = args.get('exports')
            for export in exports:
                tag = export.get('tag')
                result_key = export.get('result_key')
                task_export[tag] = results.get(result_key)
                task_export[tag]['is_artifact'] = result_key in artifact_keys
            return task_export
        except:
            return task_export
    
    def get_dag_run_export(self, dag_id: str, dag_run_id: str, use_cache=True) -> dict:
        raw_task_instances = self.airflow_manager.get_task_instances(dag_id, dag_run_id)
        job_export = {}
        for raw_task_instance in raw_task_instances:
            task_id = raw_task_instance.get('task_id')
            task_export = self.get_task_export(dag_id, dag_run_id, task_id)
            job_export.update(task_export)
        return job_export
    
    def get_task_order(self, dag_id: str, use_cache=True) -> list[str]:
        tasks = self.airflow_manager.get_dag_tasks(dag_id)
        return parse_task_order(tasks)

    def get_job_state(self, raw_dag_run):
        dag_id = raw_dag_run.get('dag_id')
        dag_run_id = raw_dag_run.get('dag_run_id')
        request_file_id = raw_dag_run.get('conf', {}).get("request_file_id")
        if not all([dag_id, dag_run_id, request_file_id]) :
            raise Exception("Invalid dag run")
        
        source = self.get_dag_run_source(request_file_id)
        exports = self.get_dag_run_export(dag_id, dag_run_id)
        
        dag_run = parse_dag_run(raw_dag_run)
        if exports:
            dag_run['artifact_tags'] = exports
        dag_run["source"] = source
        dag_run["task_order"] = self.get_task_order(dag_id)
        return dag_run

    def get_dag_runs(self, use_cache=True) -> Generator[dict, None, None]:
        dag_ids = self.get_dag_ids(use_cache)
        raw_dag_runs = self.airflow_manager.get_dag_runs(dag_ids)
        for raw_dag_run in raw_dag_runs:
            yield self.get_job_state(raw_dag_run)

    def get_dag_run(self, dag_id: str, dag_run_id: str, use_cache=True) -> dict:
        raw_dag_run = self.airflow_manager.get_dag_run(dag_id, dag_run_id)
        return self.get_job_state(raw_dag_run)
    
    def get_task_artifacts(self, dag_id: str, dag_run_id: str, task_id: str) -> dict:
        task_artifacts = {}
        filepath = self.airflow_manager.get_task_result_filepath(dag_id, dag_run_id, task_id)
        if not filepath:
            return task_artifacts
        try:
            args = self.storage.read_json(filepath)
            artifact_keys = args.get('artifact_keys')
            results = args.get('results')
            for key in results:
                results[key]['is_artifact'] = key in artifact_keys
            return results
        except:
            return task_artifacts

    def get_task_state(self, raw_task_instance):
        dag_id = raw_task_instance.get('dag_id')
        dag_run_id = raw_task_instance.get('dag_run_id')
        task_id = raw_task_instance.get('task_id')
        
        artifacts = self.get_task_artifacts(dag_id, dag_run_id, task_id)

        task_instance = parse_task_instance(raw_task_instance)
        if artifacts:
            task_instance['artifacts'] = artifacts
        return task_instance

    def get_task_instances(self, dag_id: str, dag_run_id: str, use_cache=True) -> Generator[dict, None, None]:
        raw_task_instances = self.airflow_manager.get_task_instances(dag_id, dag_run_id)
        for raw_task_instance in raw_task_instances:
            yield self.get_task_state(raw_task_instance)

    def get_task_instance(self, dag_id: str, dag_run_id: str, task_id: str, use_cache=True) -> dict:
        raw_task_instance = self.airflow_manager.get_task_instance(dag_id, dag_run_id, task_id)
        return self.get_task_state(raw_task_instance)
    
    def get_task_log(self, dag_id: str, dag_run_id: str, task_id: str, token: str | None) -> dict:
        task_instance = self.airflow_manager.get_task_instance(dag_id, dag_run_id, task_id)
        try_number = task_instance.get("try_number", 1)
        return self.airflow_manager.get_task_log(dag_id, dag_run_id, task_id, try_number, token)
