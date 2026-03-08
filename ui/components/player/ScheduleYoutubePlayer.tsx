import { useEffect, useState, useRef } from "react"
import Link from "next/link";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner } from '@fortawesome/free-solid-svg-icons';

import { useJob } from "@/hooks/job/useJob";
import { JobInfo } from "@/models/JobInfo";
import useFetchJobResult from "@/hooks/job/useFetchJobResult";
import JobProgressPanel from "./JobProgressPanel";
import KTVYoutubePlayer from "./ktv/KTVYoutubePlayer";
import { PlayerConfig } from "./YoutubeEmbbedPlayer";

interface ScheduleYoutubePlayerProps {
    jobId: string;
    config: PlayerConfig;
    handleStateChange: (event: YT.OnStateChangeEvent) => void;
    handleInfoUpdate: (data: Record<string, any>) => void;
}
export default function ScheduleYoutubePlayer({ jobId, config, handleStateChange, handleInfoUpdate }: ScheduleYoutubePlayerProps) {
    const { jobs, tasks, error, syncData } = useJob(jobId, true);
    const jobInfo = jobs[jobId];
    const { failedMessage, videoId, audioUrl, subtitles } = useFetchJobResult(jobInfo);
    const [retryCountdown, setRetryCountdown] = useState(3);

    useEffect(() => {
        if (!error)
            return;
        setRetryCountdown(3);
        let timer = setInterval(() => {
            setRetryCountdown((prev) => {
                if (prev <= 1) {
                    clearInterval(timer);
                    syncData();
                    return 3;
                }
                return prev - 1;
            });
        }, 1000);
        return () => clearInterval(timer);
    }, [error, syncData]);

    const jobLink = jobId ? <p className="mt-3">Job ID: <Link className="text-decoration-none" href={`/job?jobId=${btoa(jobId)}`} target="_blank">{jobId}</Link></p> : null;
    if (failedMessage) {
        return <div className="d-flex justify-content-center align-items-center flex-column p-2 text-danger">
            <FontAwesomeIcon icon={faTimesCircle} size="3x" />
            <h3 className="p-3">{failedMessage}</h3>
            {jobLink}
        </div>
    }
    if (error) {
        return <div className="d-flex justify-content-center align-items-center flex-column p-2">
            <FontAwesomeIcon icon={faTimesCircle} className="mb-3 text-danger" size="3x" />
            <h3 className="p-3">Failed to load job information</h3>
            <span>Retry in {retryCountdown}</span>
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
        return <JobProgressPanel
            jobInfo={jobInfo}
            tasks={tasks[jobInfo.jid] || {}}
        />
    }

    return (
        videoId && <KTVYoutubePlayer
            videoId={videoId}
            audioUrl={audioUrl}
            subtitles={subtitles}
            config={config}
            handleStateChange={handleStateChange}
            handleInfoUpdate={handleInfoUpdate}
        />
    )
}