import React, { useEffect, useState } from "react";
import { useFetchArtifact } from "@/utils/artifact";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner } from '@fortawesome/free-solid-svg-icons';

export default function ProductPreview({ jobInfo }: { jobInfo: JobInfo }) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [productUrl, setProductUrl] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [playOriginalAudio, setPlayOriginalAudio] = useState(false);

  const url = `/api/artifact/${jobInfo.jid}/plain/${jobInfo.result_artifact_index}`;
  const rawData = useFetchArtifact(url, setError);

  const videoRef = React.useRef<HTMLVideoElement>(null);
  const audioRef = React.useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (rawData) {
      const data = JSON.parse(rawData)
      setAudioUrl(`/api/artifact/${jobInfo.jid}/file/${data.vocal}`);
      setProductUrl(`/api/artifact/${jobInfo.jid}/file/${data.result}`);
    }
  }, [rawData]);

  useEffect(() => {
    if (!videoRef.current || !audioRef.current) return;
    const video = videoRef.current;
    const audio = audioRef.current;
    audio.currentTime = video.currentTime;
  }, [playOriginalAudio]);

  function syncAudio() {
    if (!videoRef.current || !audioRef.current) return;
    const video = videoRef.current;
    const audio = audioRef.current;
    video.addEventListener('play', () => {
      audio.currentTime = video.currentTime;
      audio.play();
    });
    video.addEventListener('pause', () => {
      audio.pause();
    });
    video.addEventListener('seeking', () => {
      audio.volume = 0;
    });
    video.addEventListener('seeked', () => {
      audio.currentTime = video.currentTime;
        audio.volume = video.volume;
    });
    video.addEventListener('volumechange', () => {
        audio.volume = video.volume;
    });
  }

  return <li className="list-group-item">
    <strong>Result:</strong>
    <div className="position-relative">
      {
        !error && isLoading && <div className="d-flex justify-content-center align-items-center m-auto flex-column position-absolute h-100 w-100 top-0 start-0 z-2">
          <FontAwesomeIcon icon={faSpinner} spin />
        </div>
      }
      {
        error && <div className="text-center text-danger">
          <FontAwesomeIcon icon={faTimesCircle} />
          <p>{error}</p>
        </div>
      }

      {
        !error && productUrl && <div>
          <video ref={videoRef} controls className="w-100"
            onLoadedData={() => setIsLoading(false)}
            onError={() => setError('Failed to load video')}
          >
            <source src={productUrl} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          {
            !error && !isLoading && <div className="position-absolute top-0 end-0 me-4">
              <input id="switch" type="checkbox" className="vocal-toggle" onChange={() => setPlayOriginalAudio(!playOriginalAudio)}></input>
              <label htmlFor="switch" className="vocal-toggle-label">
                <span data-on="Vocal" data-off="Karaoke"></span>
              </label>
            </div>
          }

          {
            audioUrl && <audio
              muted={!playOriginalAudio}
              ref={audioRef} className="d-none" controls src={audioUrl}
              onLoadedData={syncAudio}
            />
          }
        </div>
      }
    </div>
  </li>
}