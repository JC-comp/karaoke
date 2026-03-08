import requests
import logging
import pendulum
import threading

from functools import wraps

ARG_BUCKET_NAME = 'task-args'

class AirflowManager:
    def __init__(self, base_url: str, auth: tuple):
        self.base_url = base_url.rstrip('/')
        self.auth = auth
        self.auth_token: str | None = None
        self._auth_lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def do_auth(self):
        login_url = f"{self.base_url}/../../auth/token"
        payload = {
            "username": self.auth[0],
            "password": self.auth[1]
        }
        
        response = requests.post(login_url, json=payload)
        if response.status_code == 201:
            data = response.json()
            self.auth_token = data.get('access_token')
        else:
            raise Exception(f"Authentication failed: {response.text}")
    
    @staticmethod
    def ensure_authed(func):
        """
        Decorator-style method to ensure valid authentication before API calls.
        """
        @wraps(func)
        def wrapper(self: "AirflowManager", *args, **kwargs):
            with self._auth_lock:
                if not self.auth_token:
                    self.do_auth()
            try:
                return func(self, *args, **kwargs)
            except requests.exceptions.RequestException as e:
                if e.response and (e.response.status_code == 401 or e.response.status_code == 403):
                    self.auth_token = None
                    if kwargs.get('_retried'):
                        raise Exception("Authentication failed even after retry.")
                else:
                    raise e
                
                self.logger.info("Authentication expired, retry.")
                self.do_auth()
                kwargs['_retried'] = True
                return wrapper(self, *args, **kwargs)

        return wrapper

    def _send_request(self, method: str, path: str, **kwargs):
        """
        Internal helper to handle all Airflow API communication.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        # Ensure headers exist and include Auth
        headers = kwargs.pop('headers', {})
        headers.update({
            'Authorization': f'Bearer {self.auth_token}'
        })

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            timeout=kwargs.pop('timeout', 10),
            **kwargs
        )
        
        response.raise_for_status()
        return response.json()
    
    @ensure_authed
    def trigger_airflow_job(self, dag_id: str, request_file_id: str) -> dict:
        """
        Triggers a DAG run and returns the execution details.
        """
        return self._send_request(
            "POST",
            f"dags/{dag_id}/dagRuns",
            json={
                "conf": {
                    "request_file_id": request_file_id
                },
                "logical_date": str(pendulum.now())
            }
        )
    
    @ensure_authed
    def get_dags(self) -> list:
        response = self._send_request(
            "GET", 
            "dags"
        )
        return response.get('dags', [])
    
        
    @ensure_authed
    def get_dag_runs(self, dag_ids: list[str]) -> list:
        response = self._send_request(
            "POST", 
            f"dags/~/dagRuns/list",
            json={
                "dag_ids": dag_ids,
                "order_by": "-logical_date",
                "page_limit": 10
            }
        )
        return response.get('dag_runs', [])
    

    @ensure_authed
    def get_dag_tasks(self, dag_id: str) -> list:
        response = self._send_request(
            "GET", 
            f"dags/{dag_id}/tasks"
        )
        return response.get('tasks', [])
    
    @ensure_authed
    def get_dag_run(self, dag_id: str, dag_run_id: str) -> dict:
        return self._send_request(
            "GET", 
            f"dags/{dag_id}/dagRuns/{dag_run_id}"
        )
    
    @ensure_authed
    def patch_dag_run(self, dag_id: str, dag_run_id: str, state: str) -> dict:
        return self._send_request(
            "PATCH", 
            f"dags/{dag_id}/dagRuns/{dag_run_id}",
            json={
                "state": state
            }
        )
    
    @ensure_authed
    def clear_task_instances(self, dag_id: str, dag_run_id: str, failed_task_ids: list[str] | None) -> dict:
        return self._send_request(
            "POST", 
            f"dags/{dag_id}/clearTaskInstances",
            json={
                "dry_run": False,
                "only_failed": False,
                "dag_run_id": dag_run_id,
                "task_ids": failed_task_ids,
                "include_downstream": True
            }
        )
    
    @ensure_authed
    def get_task_instances(self, dag_id: str, dag_run_id: str) -> list:
        """
        Fetches all task instances for a specific DAG run.
        """
        data = self._send_request(
            "GET", 
            f"dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances"
        )
        return data.get('task_instances', [])

    @ensure_authed
    def get_task_instance(self, dag_id: str, dag_run_id: str, task_id: str) -> dict:
        """
        Fetches all task instances for a specific DAG run.
        """
        return self._send_request(
            "GET", 
            f"dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}"
        )
    
    @ensure_authed
    def get_task_result_filepath(self, dag_id: str, dag_run_id: str, task_id: str) -> str | None:
        """
        Get filepath of task result.
        """
        try:
            response = self._send_request(
                "GET", 
                f"dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/xcomEntries/return_value"
            )
            return response.get("value")
        except:
            return None

    @ensure_authed
    def get_task_log(self, dag_id: str, dag_run_id: str, task_id: str, try_number, token: str | None) -> dict:
        """
        Get log content.
        """
        
        log_path = f"dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}"
        if token:
            log_path += '?token=' + token
        return self._send_request("GET", log_path)