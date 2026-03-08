import Link from "next/link";

import { JobInfo } from "@/models/JobInfo";
import { TaskInfo } from "@/models/TaskInfo";
import { getStatusIcon, getStatusText } from "@/utils/icon";
import styles from './JobProgressPanel.module.css';

interface JobProgressPanel {
    jobInfo: JobInfo
    tasks: TaskInfo[]
}

function calculateTaskProgress(tasks: TaskInfo[]): number {
    if (tasks.length === 0) return 0;
    const activeStatuses = ['none', 'scheduled', 'queued', 'running'];
    const firstActiveIndex = tasks.findIndex(task => 
        activeStatuses.includes(task.status)
    );
    const completedCount = firstActiveIndex === -1 ? tasks.length : firstActiveIndex;
    return completedCount / tasks.length * 100;
}

export default function JobProgressPanel({ jobInfo, tasks }: JobProgressPanel) {
    const progress = calculateTaskProgress(tasks);

    // if the job is not finished yet, show the job status
    return <div className="d-flex flex-column justify-content-center align-items-center p-2">
        <div className="d-flex justify-content-center align-items-center p-2">
            {getStatusIcon(jobInfo.status)}
            <div className="p-2">
                {getStatusText(jobInfo.status)}
            </div>
        </div>
        <p className="mt-3">Job ID: <Link className="text-decoration-none" href={`/job?jobId=${btoa(jobInfo.jid)}`} target="_blank">{jobInfo.jid}</Link></p>
        <div className={`${styles['player-progress-container']} d-flex h-50 overflow-hidden`}>
            <div className={`${styles['player-progress-holder']} h-100`}>
                <table
                    className="table table-striped table-hover text-center w-auto"
                    style={{
                        transform: `translateY(-${progress}%)`,
                    }}
                >
                    <tbody>
                        {
                            tasks.map((task) => (
                                <tr key={task.tid}>
                                    <td>
                                        <div className='d-flex align-items-center'>
                                            <span title={task.status} className='p-2'>
                                                {getStatusIcon(task.status)}
                                            </span>
                                            <div className='text-truncate'>
                                                {task.name}
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        }
                    </tbody>
                </table>
            </div>
        </div>
    </div>
}