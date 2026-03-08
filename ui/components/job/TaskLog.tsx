import { TaskInfo } from '@/models/TaskInfo';
import styles from './TaskLog.module.css';
import { List, RowComponentProps, useDynamicRowHeight } from "react-window";
import { useDownloadLogs } from '@/hooks/job/useDownloadLogs';

function RowComponent({ index, logs, style }: RowComponentProps<{ logs: Record<string, any>[] }>) {
    const line = logs[index];
    return <div key={index} className={`d-flex flex-row ${styles['log-line']}`} style={style}>
        <code style={{ flex: "0 0 10%" }} className={styles['log-line-number']}>{index + 1}</code>
        <code style={{ flex: "0 0 15%" }} ><span className='user-select-none'>[{line.level}]</span></code>
        <code>
            <span style={{ whiteSpace: 'pre-wrap' }}>{line.event.split('\r').reverse()[0]}</span>
        </code>
    </div>
}

export default function TaskLog({ task }: { task: TaskInfo }) {
    const rowHeight = useDynamicRowHeight({
        defaultRowHeight: 25
    });
    const { logs, loading, error } = useDownloadLogs(task);
    if (loading && logs.length === 0)
        return <div className="text-center p-4">Loading logs...</div>;
    if (error)
        return <div className="text-center text-danger">{error}</div>
    if (logs.length === 0)
        return <div className="text-center text-muted">No logs available</div>;



    return <div className={styles["log-body"]}>
        <List
            rowComponent={RowComponent}
            rowCount={logs.length}
            rowHeight={rowHeight}
            rowProps={{ logs }}
        />
    </div>
}