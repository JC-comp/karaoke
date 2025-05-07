import { useEffect, useState, useRef } from "react"
import Link from "next/link";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner } from '@fortawesome/free-solid-svg-icons';
import KareokeRoomModel from '@/models/ktv';
import connectSocketIO from "@/utils/socketio";
import { JobInfo } from '@/models/job';
import { useFetchArtifact } from "@/utils/artifact";
import { capitalizeFirstLetter } from '@/utils/job';
import { getStatusIcon } from '@/utils/icon';
import { toast, Id } from "react-toastify";


declare global {
    interface Window {
        onYouTubeIframeAPIReady: (() => void) | undefined;
    }
}

export default function ScheduleEmbbedPlayer({ kareokeRoomModel, jobId }: { kareokeRoomModel: KareokeRoomModel | null; jobId: string }) {
    const playerRef = useRef<HTMLVideoElement | null>(null);
    const [jobInfo, setJobInfo] = useState<JobInfo | null>(null);
    const [resultUrl, setResultUrl] = useState<string | null>(null);
    const [productUrl, setProductUrl] = useState<string | null>(null);
    const [failedMessage, setFailedMessage] = useState<string | null>(null);
    const [checkInteracted, setCheckInteracted] = useState<Id | null>(null);
    const rawData = useFetchArtifact(resultUrl, setFailedMessage);

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
        if (jobInfo.result_artifact_index < 0) return;
        const url = `/api/artifact/${jobInfo.jid}/${jobInfo.result_artifact_index}`;
        setResultUrl(url);
    }, [jobInfo]);


    useEffect(() => {
        if (!rawData) return;
        if (!jobInfo) return;

        const data = JSON.parse(rawData)
        setProductUrl(`/api/artifact/${jobInfo.jid}/${data.result}`);
    }, [rawData]);

    useEffect(() => {
        if (!kareokeRoomModel) return;
        const player = playerRef.current;
        if (!player) return;
        if (checkInteracted) return;

        if (kareokeRoomModel.is_playing) {
            player.play().catch(() => {
                onVideoReady();
            });
        }
        else
            player.pause();
    });

    useEffect(() => {
        if (checkInteracted == null) return;
        const interval = setInterval(() => {
            if (kareokeRoomModel?.is_playing === false) {
                toast.dismiss(checkInteracted);
                setCheckInteracted(null);
            } else {
                playerRef.current?.play().then(() => {
                    toast.dismiss(checkInteracted);
                    setCheckInteracted(null);
                }).catch(() => {
                    // wait for user interaction
                });
            }
        }, 1000);
        return () => {
            clearInterval(interval);
        }
    }, [checkInteracted]);

    const onVideoReady = () => {
        const video = playerRef.current;
        if (!video) return;
        if (checkInteracted) return;
        if (kareokeRoomModel?.is_playing)
            video.play().catch((error) => {
                if (error.name === 'NotAllowedError') {
                    const toastId = toast.warn('Please interact with the page to start playback.', {
                        autoClose: false,
                        closeOnClick: false,
                    });
                    setCheckInteracted(toastId);
                }
            });
    }

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

    if (!productUrl) {
        // if the job is finished successfully and the product URL is still loading
        if (resultUrl) {
            return <div className="d-flex justify-content-center align-items-center flex-column p-2">
                <FontAwesomeIcon icon={faSpinner} spin size="3x" />
                <h3 className="p-3">Loading Video...</h3>
                {jobLink}
            </div>
        }
        if (Object.keys(jobInfo.tasks).length == 0) {
            return <div className="d-flex flex-column justify-content-center align-items-center p-2">
                <div className="d-flex justify-content-center align-items-center p-2">
                    {getStatusIcon(jobInfo.status)}
                    <div className="p-2">
                        {capitalizeFirstLetter(jobInfo.status)}
                    </div>
                </div>
                <div>
                    Waiting for conversion to finish...
                </div>
                {jobLink}
            </div>
        } else {
            return <div className="d-flex flex-column align-items-center justify-content-center">
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
    }

    return (
        productUrl && <video ref={playerRef} className="w-100" controls
            onError={() => setFailedMessage('Failed to load video')}
            onLoadedData={onVideoReady}
            onEnded={() => kareokeRoomModel?.moveToNextItem()}
        >
            <source src={productUrl} type="video/mp4" />
            Your browser does not support the video tag.
        </video>
    )
}