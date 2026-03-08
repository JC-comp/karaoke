import { JobInfo } from "@/models/JobInfo"
import { TaskInfo } from "@/models/TaskInfo";
import JobInfoCard from "./JobInfoCard";
import MediaMetadataCard from "./MediaMetadataCard";
import TaskPanel from "./TaskPanel";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner, faPaperclip, IconDefinition, faExpand, faCompress } from '@fortawesome/free-solid-svg-icons';

interface JobPanelProps {
    jobInfo: JobInfo;
    tasks: Record<string, TaskInfo>;
}

export default function JobPanel({ jobInfo, tasks }: JobPanelProps) {
    const hasTasks = Object.keys(tasks).length > 0;
    return <div className="d-flex">
        <div className="col-3 overflow-auto">
            <JobInfoCard jobInfo={jobInfo} />
            <MediaMetadataCard jobInfo={jobInfo} />
        </div>
        <div className="col-9 overflow-auto">
            {
                hasTasks ? <TaskPanel jobInfo={jobInfo} tasks={tasks} /> :
                    <div className="flex-column text-center">
                        <FontAwesomeIcon icon={faSpinner} className="mb-3" size="3x" spin={true} />
                        <p className="lead">Loading task information...</p>
                    </div>
            }
        </div>
    </div>
}