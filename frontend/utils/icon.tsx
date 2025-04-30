import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
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

export const getStatusColor = (status: Task['status'] | JobInfo['status']) => {
    switch (status) {
        case 'pending':
            return 'text-warning';
        case 'queued':
            return 'text-info';
        case 'created':
            return 'text-primary';
        case 'running':
            return 'text-primary';
        case 'completed':
            return 'text-success';
        case 'failed':
            return 'text-danger';
        case 'soft_failed':
            return 'text-warning';
        case 'skipped':
            return 'text-warning';
        case 'interrupting':
            return 'text-info';
        case 'canceled':
        case 'interrupted':
            return 'text-danger';
        default:
            return '';
    }
}

export const getStatusProps = (status: Task['status'] | JobInfo['status']) => {
    switch (status) {
        case 'running':
            return {
                spin: true,
            }
        case 'queued':
        case 'created':
        case 'interrupting':
            return {
                fade: true,
            }
        default:
            return {};
    }
}

export const getStatusIcon = (status: Task['status'] | JobInfo['status']) => {
    var icon;
    switch (status) {
        case 'pending':
            icon = faPauseCircle;
            break;
        case 'queued':
            icon = faShareFromSquare;
            break;
        case 'created':
            icon = faLink;
            break;
        case 'running':
            icon = faSpinner;
            break;
        case 'completed':
            icon = faCheckCircle;
            break;
        case 'soft_failed':
            icon = faCircleExclamation;
            break;
        case 'failed':
            icon = faTimesCircle;
            break;
        case 'skipped':
            icon = faForward;
            break;
        case 'interrupting':
            icon = faStop;
            break;
        case 'canceled':
            icon = faBan;
            break;
        case 'interrupted':
            icon = faHand;
            break;
        default:
            icon = null;
    }
    if (icon) {
        return <FontAwesomeIcon icon={icon} {...getStatusProps(status)} className={getStatusColor(status)} />;
    }
    return null;
};