import React, { useEffect, useState } from "react";
import { useFetchArtifact } from "@/utils/artifact";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner } from '@fortawesome/free-solid-svg-icons';
import KTVYoutubePlayer from "@/components/players/KTVYoutubePlayer";

export default function ProductPreview({ jobInfo }: { jobInfo: JobInfo }) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [subtitles, setSubtitles] = useState<Subtitle[]>([]);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const url = `/api/artifact/${jobInfo.jid}/${jobInfo.result_artifact_index}`;
  const rawData = useFetchArtifact(url, setError);

  const videoId = new URL(jobInfo.media.source).searchParams.get("v");

  useEffect(() => {
    if (rawData) {
      const data = JSON.parse(rawData);
      setAudioUrl(`/api/artifact/${jobInfo.jid}/${data.instrumental}`);
      setSubtitles(data.subtitle);
      setIsLoading(false);
    }
  }, [rawData]);

  useEffect(() => {
    if (!videoId)
      setError("Invalid video ID");
  }, []);

  return <li className="list-group-item">
    <strong>Result:</strong>
    <div className="position-relative">
      {
        error && <div className="text-center text-danger">
          <FontAwesomeIcon icon={faTimesCircle} />
          <p>{error}</p>
        </div>
      }
      {
        !error && isLoading && <div className="d-flex justify-content-center align-items-center m-auto flex-column position-absolute h-100 w-100 top-0 start-0 z-2">
          <FontAwesomeIcon icon={faSpinner} spin />
        </div>
      }
      {
        !error && videoId && audioUrl && <KTVYoutubePlayer
          shouldPlay={false}
          videoId={videoId}
          audioUrl={audioUrl}
          subtitles={subtitles}
        />
      }
    </div>
  </li>
}