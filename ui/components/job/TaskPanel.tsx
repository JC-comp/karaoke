import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner, faPaperclip, IconDefinition, faExpand, faCompress } from '@fortawesome/free-solid-svg-icons';
import { JobInfo } from "@/models/JobInfo"
import { TaskInfo } from "@/models/TaskInfo";
import { getStatusColor, getStatusIcon, getStatusText } from "@/utils/icon";
import styles from './TaskPanel.module.css';
import TaskLog from './TaskLog';
import ArtifactPanel from '../artifact/ArtifactPanel';
import { useEffect, useRef, useState } from 'react';

const TaskItem = ({ task, artifacts }: { task: TaskInfo, artifacts: Record<string, Artifact> }) => {
    const [visible, setVisible] = useState(false);
    const collapseRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const element = collapseRef.current;
        if (element == null) return;
        const handleHidden = () => setVisible(false);
        const handleShow = () => setVisible(true);
        element.addEventListener('hide.bs.collapse', handleHidden);
        element.addEventListener('show.bs.collapse', handleShow);
        return () => {
            element.removeEventListener('hide.bs.collapse', handleHidden)
            element.removeEventListener('show.bs.collapse', handleShow)
        };
    }, [task]);

    return (<div ref={collapseRef} id={`collapse${task.tid}`} className="accordion-collapse collapse" aria-labelledby={`heading${task.tid}`} data-bs-parent="#accordionTasks">
        <div className={"accordion-body"}>
            <div className='d-flex flex-column'>
                {
                    task.hasArtifact() &&
                    <ArtifactPanel task={task} artifacts={artifacts} visible={visible} />
                }
                {
                    visible && <TaskLog task={task} />
                }
            </div>
        </div>
    </div>
    );
};

interface TaskPanelProps {
    jobInfo: JobInfo;
    tasks: Record<string, TaskInfo>;
}

export default function TaskPanel({ jobInfo, tasks }: TaskPanelProps) {
    const artifacts = Object.values(tasks).reduce((acc, task) => ({
        ...acc,
        ...task.artifacts
    }), {} as Record<string, Artifact>);
    return <div className="accordion" id="accordionTasks">
        {
            Object.values(tasks).map((task) => (
                <div className="accordion-item" key={task.tid}>
                    <div className="accordion-header" id={`heading${task.tid}`}>
                        <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target={`#collapse${task.tid}`} aria-expanded="false" aria-controls={`collapse${task.tid}`}>
                            {getStatusIcon(task.status)}
                            <span className={`${styles["status-text"]} badge ${getStatusColor(task.status)} flex-shrink-0`}>
                                {getStatusText(task.status)}
                            </span>
                            <div className='d-flex flex-column overflow-hidden'>
                                <span>
                                    {
                                        task.hasArtifact() && (
                                            <FontAwesomeIcon icon={faPaperclip} className="me-2" />
                                        )
                                    }
                                    {task.name}
                                </span>
                            </div>
                        </button>
                    </div>
                    <TaskItem task={task} artifacts={artifacts} />
                </div>
            ))
        }
    </div >
}