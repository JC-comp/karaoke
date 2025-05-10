import multiprocessing
import argparse

from .binder.scheduler import SchedulerBinder
from .binder.command import CommandBinder
from .pipeline.youtube import YoutubePipeline
from ..utils.job import JobType

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    parser = argparse.ArgumentParser(description='Worker')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--jobId', type=str, help='Job ID from Scheduler')
    group.add_argument('--url', type=str, help='URL to download')
    group.add_argument('--filepath', type=str, help='Input file path')  

    args = parser.parse_args()
    if args.jobId:
        binder = SchedulerBinder(args.jobId)
    else:
        binder = CommandBinder(args.url, args.filepath)
        
    binder.bind()
    job = binder.get_job_info()
    binder.listen()
    try:
        if job.job_type == JobType.YOUTUBE:
            pipeline = YoutubePipeline(job)
        else:
            raise ValueError(f'Unsupported job type: {job.job_type}')

        pipeline.start()
    except Exception as e:
        binder.close()
        raise e
