import React, { useState, useEffect, useRef } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faPause, faSpinner, faPaperclip, IconDefinition, faExpand, faCompress } from '@fortawesome/free-solid-svg-icons';
import { JobInfo } from "@/models/JobInfo";
import useFullscreen from '@/hooks/useFullscreen';
import useFetchJobResult from '@/hooks/job/useFetchJobResult';
import KTVYoutubePlayer from '../player/ktv/KTVYoutubePlayer';

function Product({ jobInfo }: { jobInfo: JobInfo }) {
    const { failedMessage, videoId, audioUrl, subtitles } = useFetchJobResult(jobInfo);
    const [vocal, setVocal] = useState(false);
    const [playing, setPlaying] = useState(false);
    
    if (failedMessage || !videoId)
        return <div className="text-center text-danger">
            <FontAwesomeIcon icon={faTimesCircle} />
            <p>{failedMessage}</p>
        </div>
    if (jobInfo.isRunning())
        return <div className="text-center text-primary p-4">
            <FontAwesomeIcon icon={faPause} bounce />
        </div>
    if (!audioUrl || !subtitles) {
        return <div className="d-flex justify-content-center align-items-center m-auto flex-column position-absolute h-100 w-100 top-0 start-0 z-2">
            <FontAwesomeIcon icon={faSpinner} spin />
        </div>
    }

    const config = {
        unmanaged: true,
        is_playing: playing,
        is_vocal_on: vocal
    }

    function handleInfoUpdate(info: Record<string, any>) {
        if (info.muted !== undefined) {
            setVocal(!info.muted);
        }
    }
    
    function handleStateChange(event: YT.OnStateChangeEvent) {
        setPlaying(event.data == YT.PlayerState.PLAYING);
    }

    return <KTVYoutubePlayer
        videoId={videoId}
        audioUrl={audioUrl}
        subtitles={subtitles}
        config={config}
        handleStateChange={handleStateChange}
        handleInfoUpdate={handleInfoUpdate}
    />
}

export default function ProductPreview({ jobInfo }: { jobInfo: JobInfo }) {
    const containerRef = useRef<HTMLLIElement>(null);
    const { isFullscreen, toggle } = useFullscreen(containerRef);

    return <li ref={containerRef} className="list-group-item">
        <div className="d-flex flex-column w-100 h-100">
            <div>
                <strong>Result:</strong>
                <button className='btn btn-outline-info btn-sm mx-2' onClick={toggle}>
                    <FontAwesomeIcon icon={isFullscreen ? faCompress : faExpand} size='sm' />
                </button>
            </div>
            <div className='flex-grow-1'>
                <Product jobInfo={jobInfo} />
            </div>
        </div>
    </li>
}