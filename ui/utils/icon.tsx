import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
    faBorderNone,
    faPauseCircle,
    faShareFromSquare,
    faCheckCircle,
    faTimesCircle,
    faCircleExclamation,
    faSpinner,
    faStop,
    faLink,
    faForward,
    faBan,
    faHand
} from '@fortawesome/free-solid-svg-icons';
import { JobInfo } from '@/models/JobInfo';
import { TaskInfo } from '@/models/TaskInfo';


export const getStatusColor = (status: JobInfo['status'] | TaskInfo['status']) => {
    switch (status) {
        case 'none':
            return 'text-secondary';
        case 'queued':
            return 'text-info';
        case 'running':
            return 'text-primary';
        case 'success':
            return 'text-success';
        case 'failed':
            return 'text-danger';
        case 'skipped':
            return 'text-warning';
        default:
            return '';
    }
}

export const getStatusProps = (status: JobInfo['status'] | TaskInfo['status']) => {
    switch (status) {
        case 'running':
            return {
                spin: true,
            }
        case 'none':
        case 'queued':
            return {
                fade: true,
            }
        default:
            return {};
    }
}

export const getStatusIcon = (status: JobInfo['status'] | TaskInfo['status']) => {
    var icon;
    switch (status) {
        case 'none':
            icon = faBorderNone;
            break;
        case 'queued':
        case 'scheduled':
            icon = faShareFromSquare;
            break;
        case 'running':
            icon = faSpinner;
            break;
        case 'success':
            icon = faCheckCircle;
            break;
        case 'failed':
            icon = faTimesCircle;
            break;
        case 'skipped':
            icon = faForward;
            break;
        default:
            icon = null;
    }
    if (icon) {
        return <FontAwesomeIcon icon={icon} {...getStatusProps(status)} className={getStatusColor(status)} />;
    }
    return null;
};

export const getStatusText = (status: JobInfo['status'] | TaskInfo['status']) => {
    if (!status)
        return '';
    return status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ');
}