import os
import socket
import threading
import json

from .job import Job, CacheJob
from .slave.manager import SlaveManager
from ...utils.connection import Connection as Client
from ...utils.config import get_logger, Config
from ...utils.job import JobStatus

class Scheduler:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger = get_logger(__name__, config.log_level)
        self.job_list: dict[str, CacheJob] = self.load_job_list()
        self.client_list: list[Client] = []
        self.slave_manager = SlaveManager(config)
        self.process_lock = threading.Lock()
        self.running_job = None

    def load_job_list(self) -> list[CacheJob]:
        """
        Load the job list from the media path.
        """
        job_list = {}
        for file in os.listdir(self.config.media_path):
            if file.endswith('.json'):
                with open(os.path.join(self.config.media_path, file), 'r') as f:
                    try:
                        self.logger.info(f"Loading job {file}")
                        job_info = json.load(f)
                        job = CacheJob(**job_info)
                        job_list[job.jid] = job
                    except Exception as e:
                        self.logger.error(f"Error loading job {file}: {e}", exc_info=True)
                        continue
        return job_list

    def spwawn_process(self, job: Job) -> None:
        """
        Spawn a new process to handle the job.
        We use the lock to ensure that only one process is spawned at a time.
        """
        try:
            # TODO: Implement job level progress message
            job.update(status=JobStatus.QUEUED)
            with self.process_lock:
                # TODO: Implement a timeout for the process submission
                process = self.slave_manager.submit(job.jid)
                self.logger.info(f'Spawned process {process.pid}')
                
                job.attach(process)
                self.running_job = job
                process.wait()
                self.logger.info(f"Process {job.jid} finished with return code {process.returncode}")
        except Exception as e:
            self.logger.error(f"Error spawning process: {e}", exc_info=True)
        finally:
            self.running_job = None
        
        # Handle process exit
        job.done()
    
    def clean_job_list(self) -> None:
        """
        Clean up the job list by removing finished jobs.
        """
        if (len(self.job_list) < self.config.max_daemon_jobs):
            return
        for jobId in list(self.job_list.keys()):
            if self.job_list[jobId].is_finished():
                del self.job_list[jobId]
                self.logger.info(f"Removed finished job {jobId} from job list")
                break

    def create_job(self, client: Client, job_info: dict) -> None:
        """
        Create a job from the client request.
        Spawn a new process to handle the job.
        Send the job information back to the client on success.
        """
        try:
            self.clean_job_list()
            job = Job(**job_info)
            self.job_list[job.jid] = job
            for listening_client in self.client_list:
                job.add_listener(listening_client)
        except Exception as e:
            client.log(self.logger.error, f"Error creating job: {e}", exc_info=True)
            client.error('Failed to create job: ' + str(e))
            return
        
        threading.Thread(target=self.spwawn_process, args=(job,)).start()
        client.log(self.logger.info, f'Created job {job.jid}')
        client.send(json.dumps(job.serialize()))
    
    def get_job(self, jobId: str) -> Job:
        """
        Get a job from the job list or in cache.
        """
        if jobId in self.job_list:
            return self.job_list[jobId]
        location = os.path.join(self.config.media_path, jobId + '.json')
        if os.path.exists(location):
            with open(location, 'r') as f:
                job_info = json.load(f)
                job = CacheJob(**job_info)
                return job
        return None

    def listen_for_job_updates(self, client: Client, jobId: str) -> None:
        """
        Register update listener and wait until client disconnects.
        """
        job = self.get_job(jobId)
        if job is None:
            client.log(self.logger.error, f"Job {jobId} not found")
            client.error('Job not found')
            return
        
        job.add_listener(client)
        try:
            while True:
                status = client.json_idle()
                if 'bye' in status:
                    client.log(self.logger.info, "Client sent bye")
                    break
                client.log(self.logger.info, "Received unexpected message from client")
        except Exception as e:
            client.log(self.logger.error, f"Error reading from client: {e}")
        finally:
            job.remove_listener(client)

    def listen_for_all_job_updates(self, client: Client) -> None:
        """
        Register update listener for all jobs and wait until client disconnects.
        """
        self.client_list.append(client)
        for job in self.job_list.values():
            job.add_listener(client)
        
        try:
            while True:
                status = client.json_idle()
                if 'bye' in status:
                    client.log(self.logger.info, "Client sent bye")
                    break
                client.log(self.logger.info, "Received unexpected message from client")
        except Exception as e:
            client.log(self.logger.error, f"Error reading from client: {e}")
        finally:
            self.client_list.remove(client)
            for job in self.job_list.values():
                job.remove_listener(client)

    def handle_artifact(self, client: Client, jobId: str, artifact: int) -> None:
        """
        Handle artifact query from client.
        """
        job = self.get_job(jobId)
        if job is None:
            client.log(self.logger.error, f"Job {jobId} not found")
            client.error('Job not found')
            return
        try:
            artifact = job.get_artifact(artifact)
        except IndexError:
            client.log(self.logger.error, f"Artifact {artifact} not found")
            client.error('Artifact not found')
            return
        client.log(self.logger.debug, f"Sending artifact {artifact}")
        client.send(json.dumps({
            'artifact_type': artifact[0],
            'artifact': artifact[1]
        }))
        
    def handle_user(self, client: Client, client_info: dict) -> None:
        """
        Handle a user client connection.
        """
        action = client_info.get('action') 
        if action == 'submit':
            job_info = client_info.get('job')
            self.create_job(client, job_info)
        elif action == 'query':
            jobId = client_info.get('jobId')
            if jobId == '*':
                self.listen_for_all_job_updates(client)
            else:
                self.listen_for_job_updates(client, jobId)
        elif action == 'artifact':
            jobId = client_info.get('jobId')
            artifact = int(client_info.get('artifact'))
            self.handle_artifact(client, jobId, artifact)
        else:
            self.logger.warning(f"Unknown action from client: {action}")
            client.error('Unknown action: ' + str(action))

    def handle_worker(self, client: Client, client_info: dict) -> None:
        """
        Handle a worker client connection.
        Keep the connection alive and listen for job updates.
        """
        jobId = client_info.get('jobId')
        client.log(self.logger.debug, f"Finding jobId = {jobId}")
        if jobId not in self.job_list:
            client.log(self.logger.error, f"Job {jobId} not found")
            client.error('Job not found')
            return
        client.log(self.logger.debug, f"Found jobId = {jobId}, sending job info")
        client.send(json.dumps(self.job_list[jobId].serialize()))

        while True:
            progress = client.json_idle()
            if 'bye' in progress:
                client.log(self.logger.info, "Worker sent bye")
                break
            client.log(self.logger.debug, "Received progress update")
            self.job_list[jobId].update(**progress)
    
    def handle_slave(self, client: Client, client_info: dict) -> None:
        """
        Handle a slave client connection.
        """
        slave_id = client_info.get('slaveId')
        self.slave_manager.add_slave(slave_id, client)

    def handle_connection(self, client: Client) -> None:
        """
        Handle a new client connection.
        """
        try:
            client_info = client.json()
            client.log(self.logger.info, f"Received client info: {client_info}")
            role = client_info.get('role')
            if role == 'user':
                self.handle_user(client, client_info)
            elif role == 'worker':
                self.handle_worker(client, client_info)
            elif role == 'slave':
                self.handle_slave(client, client_info)
            else:
                client.log(self.logger.warning, f"Unknown role received from client: {role}")
        except Exception as e:
            client.log(self.logger.error, f"Error handling client: {e}", exc_info=True)
            try:
                client.error(f"Error: {e}")
            except Exception as e:
                client.log(self.logger.error, f"Error sending error message to client: {e}")
        finally:
            client.log(self.logger.debug, "Closing client")
            client.close()

    def run(self, host: str = '0.0.0.0', port: int = 8201) -> None:
        """
        Run the scheduler server.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen()
        self.logger.info(f"Scheduler: Listening on {host}:{port}")
        try:
            while True:
                client_socket, client_address = server_socket.accept()
                self.logger.debug("Accepted a new client connection from {}".format(client_address))
                client = Client(client_socket, server_side=True)
                client_thread = threading.Thread(target=self.handle_connection, args=(client, ))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            self.logger.info("Scheduler: Shutting down...")
        finally:
            self.logger.info("Scheduler: Closing the server socket...")
            server_socket.close()

if __name__ == "__main__":
    config = Config()
    scheduler = Scheduler(config)
    scheduler.run(host=config.scheduler_host, port=config.scheduler_port)