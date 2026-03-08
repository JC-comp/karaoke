import Moment from 'react-moment';
import { JobInfo } from "@/models/JobInfo";
import { getStatusIcon, getStatusText } from '@/utils/icon';
import { timeDiff } from '@/utils/time';
import JobActionController from './JobActionController';
import ProductPreview from './ProductPreview';

interface JobInfoCardProps {
    jobInfo: JobInfo;
}

export default function JobInfoCard({ jobInfo }: JobInfoCardProps) {
    return <div className="card">
        <div className="card-body">
            <h5 className="card-title">Job Information</h5>
            <ul className='list-group list-group-flush'>
                <li className="list-group-item">
                    <strong>Created At:</strong> <Moment fromNow withTitle date={jobInfo.created_at} />
                </li>
                {
                    jobInfo.started_at && (
                        <li className="list-group-item">
                            <strong>Queued: </strong>
                            {timeDiff(jobInfo.started_at, jobInfo.created_at)}
                        </li>
                    )
                }
                {
                    jobInfo.started_at && jobInfo.finished_at && (
                        <li className="list-group-item">
                            <strong>Duration: </strong>
                            {timeDiff(jobInfo.started_at, jobInfo.finished_at)}
                        </li>
                    )
                }
                <li className="list-group-item">
                    <strong>Status:</strong> {getStatusIcon(jobInfo.status)} {getStatusText(jobInfo.status)}
                </li>
                <li className="list-group-item">
                    <strong>Action:</strong>
                    <JobActionController jobInfo={jobInfo} />
                </li>
                <ProductPreview jobInfo={jobInfo} />
            </ul>
        </div>
    </div>
}