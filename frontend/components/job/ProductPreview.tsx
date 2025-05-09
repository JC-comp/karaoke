import React, { useEffect, useState } from "react";
import { useFetchArtifact } from "@/utils/artifact";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner, faPause } from '@fortawesome/free-solid-svg-icons';
import KTVYoutubePlayer from "@/components/players/KTVYoutubePlayer";

export default function ProductPreview({ jobInfo }: { jobInfo: JobInfo }) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [subtitles, setSubtitles] = useState<Subtitle[]>([]);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [subtitleUrl, setSubtitleUrl] = useState<string | null>(null);
  const rawData = useFetchArtifact(subtitleUrl, setError);

  const videoId = new URL(jobInfo.media.source).searchParams.get("v");

  useEffect(() => {
    if (rawData) {
      const data = JSON.parse(rawData);
      setSubtitles(data);
      setIsLoading(false);
    }
  }, [rawData]);

  useEffect(() => {
    if (!videoId)
      setError("Invalid video ID");
  }, []);

  useEffect(() => {
    if (jobInfo.artifact_tags.Instrumental)
      setAudioUrl(`/api/artifact/${jobInfo.jid}/${jobInfo.artifact_tags.Instrumental}`);
    if (jobInfo.artifact_tags.subtitles)
      setSubtitleUrl(`/api/artifact/${jobInfo.jid}/${jobInfo.artifact_tags.subtitles}`);

    if (!jobInfo.isRunning()) {
      if (!('subtitles' in jobInfo.artifact_tags))
        setError("Subtitles are not generated for this job");
      if (!('Instrumental' in jobInfo.artifact_tags))
        setError("Instrumental is not generated for this job");
    }
  }, [jobInfo]);

  if (error) {
    return <div className="text-center text-danger">
      <FontAwesomeIcon icon={faTimesCircle} />
      <p>{error}</p>
    </div>
  }

  if (jobInfo.isRunning()) {
    return <div className="text-center text-primary">
      <FontAwesomeIcon icon={faPause} bounce />
    </div>
  }

  if (isLoading) {
    return <div className="d-flex justify-content-center align-items-center m-auto flex-column position-absolute h-100 w-100 top-0 start-0 z-2">
      <FontAwesomeIcon icon={faSpinner} spin />
    </div>
  }

  return (videoId && audioUrl && <KTVYoutubePlayer
    shouldPlay={false}
    videoId={videoId}
    audioUrl={audioUrl}
    subtitles={subtitles}
  />
  )
}