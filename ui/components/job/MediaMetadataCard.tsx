import { JobInfo } from "@/models/JobInfo";

interface MediaMetadataCardProps {
    jobInfo: JobInfo;
}

export default function MediaMetadataCard({ jobInfo }: MediaMetadataCardProps) {
    return <div className="card">
        <div className="card-body">
            <h5 className="card-title">Media Metadata</h5>
            {
                jobInfo.artifact_tags.metadata &&
                <ul className='list-group list-group-flush'>
                    <li className="list-group-item">
                        <strong>ID:</strong> {jobInfo.artifact_tags.metadata.value.id}
                    </li>
                    <li className="list-group-item">
                        <strong>Source:</strong> {jobInfo.source.url?.value}
                    </li>
                    <li className="list-group-item">
                        <strong>Title:</strong> {jobInfo.artifact_tags.metadata.value.title}
                    </li>
                    <li className="list-group-item">
                        <strong>Channel:</strong> {jobInfo.artifact_tags.metadata.value.channel}
                    </li>
                    <li className="list-group-item">
                        <strong>Duration:</strong> {
                            jobInfo.artifact_tags.metadata.value.duration ?? ''
                        }
                    </li>
                </ul>
            }
        </div>
    </div>
}