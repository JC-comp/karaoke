import { useEffect, useState, useRef } from "react"
import Link from "next/link";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner } from '@fortawesome/free-solid-svg-icons';
import KareokeRoomModel from '@/models/ktv';
import KTVYoutubePlayer from "@/components/players/KTVYoutubePlayer";
import { JobInfo } from '@/models/job';
import connectSocketIO from "@/utils/socketio";
import { useFetchArtifact } from "@/utils/artifact";
import { capitalizeFirstLetter } from '@/utils/job';
import { getStatusIcon } from '@/utils/icon';

interface ScheduleYoutubePlayerProps {
    jobId: string;
    shouldPlay: boolean;
    onPlayerReady?: (event: YT.PlayerEvent) => void;
    onPlayerStateChange?: (event: YT.OnStateChangeEvent) => void;
    onStateChange?: (player: YT.Player) => void;
}

export default function ScheduleYoutubePlayer({ jobId, shouldPlay, onPlayerReady, onPlayerStateChange, onStateChange }: ScheduleYoutubePlayerProps) {
    const playerRef = useRef<HTMLVideoElement | null>(null);
    const [jobInfo, setJobInfo] = useState<JobInfo | null>(null);
    const [resultUrl, setResultUrl] = useState<string | null>(null);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const [subtitles, setSubtitles] = useState<Subtitle[]>([]);
    const [failedMessage, setFailedMessage] = useState<string | null>(null);
    const rawData = useFetchArtifact(resultUrl, setFailedMessage);
    const videoId = jobInfo ? new URL(jobInfo.media.source).searchParams.get("v") : null;

    useEffect(() => {
        if (!jobId) return
        const onError = (error: string) => {
            setFailedMessage(error);
            setJobInfo(null);
        }

        const preJoin = () => {
            setFailedMessage(null);
            setJobInfo(null);
        }

        const { socket, unsubscribe } = connectSocketIO('/job', jobId, preJoin, onError);

        socket.on('progress', (parsedData) => {
            setFailedMessage(null);
            setJobInfo(JobInfo.fromJSON(parsedData));
        });

        return () => {
            unsubscribe();
        }
    }, [jobId]);

    useEffect(() => {
        if (!jobInfo) return;
        if (!videoId) setFailedMessage("Invalid video ID");
        if (jobInfo.result_artifact_index < 0) return;
        const url = `/api/artifact/${jobInfo.jid}/${jobInfo.result_artifact_index}`;
        setResultUrl(url);
    }, [jobInfo]);


    useEffect(() => {
        if (!rawData) return;
        if (!jobInfo) return;

        const data = JSON.parse(rawData)
        setAudioUrl(`/api/artifact/${jobInfo.jid}/${data.instrumental}`);
        setSubtitles(data.subtitle);
    }, [rawData]);

    const jobLink = jobId ? <p className="mt-3">Job ID: <Link className="text-decoration-none" href={`/job?jobId=${jobId}`} target="_blank">{jobId}</Link></p> : null;


    if (failedMessage) {
        return <div className="d-flex justify-content-center align-items-center flex-column p-2 text-danger">
            <FontAwesomeIcon icon={faTimesCircle} size="3x" />
            <h3 className="p-3">{failedMessage}</h3>
            {jobLink}
        </div>
    }

    if (!jobInfo) {
        return <div className="d-flex justify-content-center align-items-center flex-column p-2">
            <FontAwesomeIcon icon={faSpinner} spin size="3x" />
            <h3 className="p-3">Loading Job Info...</h3>
            {jobLink}
        </div>
    }

    if (!audioUrl) {
        // if the job is finished successfully and the product URL is still loading
        if (resultUrl) {
            return <div className="d-flex justify-content-center align-items-center flex-column p-2">
                <FontAwesomeIcon icon={faSpinner} spin size="3x" />
                <h3 className="p-3">Loading Video...</h3>
                {jobLink}
            </div>
        }
        // if the job is not finished yet, show the job status
        return <div className="d-flex flex-column justify-content-center align-items-center p-2">
            <div className="d-flex justify-content-center align-items-center p-2">
                {getStatusIcon(jobInfo.status)}
                <div className="p-2">
                    {capitalizeFirstLetter(jobInfo.status)}
                </div>
            </div>
            {jobLink}
            <div className="player-progress-container d-flex h-50 overflow-hidden">
                <div className="player-progress-holder h-100">
                    <table
                        className="table table-striped table-hover text-center w-auto"
                        style={{
                            transform: `translateY(-${(Math.min(Object.values(jobInfo.tasks).length, ...Object.values(jobInfo.tasks).map((task, idx) => ['pending', 'queued', 'running', 'interrupted'].includes(task.status) ? idx : -1).filter(idx => idx !== -1)) / Object.values(jobInfo.tasks).length) * 100}%)`,
                        }}
                    >
                        <tbody>
                            {
                                Object.values(jobInfo.tasks).map((task) => (
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

    return (
        videoId && <KTVYoutubePlayer
            videoId={videoId}
            shouldPlay={shouldPlay}
            audioUrl={audioUrl}
            subtitles={subtitles}
            onPlayerReady={onPlayerReady}
            onPlayerStateChange={onPlayerStateChange}
            onStateChange={onStateChange}
        />
    )
}