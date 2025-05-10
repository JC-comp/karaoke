import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlay, faStop, faPause } from '@fortawesome/free-solid-svg-icons';

import RersponsiveButton from '@/components/RersponsiveButton';
import { toast } from 'react-toastify';

export default function JobActionController({ jobInfo }: { jobInfo: JobInfo }) {
    function update(action: string) {
        const form = new FormData();
        form.append('action', action);
        return fetch(`/api/job/${jobInfo.jid}`, {
            method: 'POST',
            body: form
        }).then((response) => {
            return response.json().catch(() => {
                throw new Error(response.statusText || 'Failed to parse response: ' + response.status.toString());
            });
        }).then((data) => {
            if (!data.success)
                throw new Error(data.message);
        }).catch((error) => {
            toast.error(error.message);
        });
    }
    return <div className="btn-group mx-2" role="group" aria-label="Basic example">
        <RersponsiveButton
            className={`btn btn-secondary disabled`}
            icon={<FontAwesomeIcon icon={faPlay} />}
            onClick={() => { return new Promise((resolve) => { setTimeout(resolve, 1000) }) }}
            children={null}
        />
        <RersponsiveButton
            className={`btn btn-secondary disabled`}
            icon={<FontAwesomeIcon icon={faPause} />}
            onClick={() => { return new Promise((resolve) => { setTimeout(resolve, 1000) }) }}
            children={null}
        />
        <RersponsiveButton
            className={`btn ${jobInfo.isRunning() ? 'btn-primary' : 'btn-secondary disabled'}`}
            icon={<FontAwesomeIcon icon={faStop} />}
            onClick={() => update('stop')}
            children={null}
        />
    </div>
}