import { useEffect, useState } from "react"
import { JobInfo } from "@/models/JobInfo";
import { Subtitle } from "@/types/subtitle";
import { useFileLoader } from "../useFileLoader";

const initialSubtitle: Subtitle = {
    start: 0,
    end: 60 * 15,
    alignX: "center",
    alignY: "bottom",
    y: 0.9 / 15 * 0.33,
    font_size: 0.9 / 15,
    words: [
        {
            start: 0,
            end: 0,
            text: "Generating lyrics...",
        }
    ]
}

const failedSubtitle: Subtitle = {
    ...initialSubtitle,
    words: [
        {
            start: 0,
            end: 0,
            text: "Failed to generate lyrics",
        }
    ]
}

export default function useFetchJobResult(jobInfo: JobInfo | null) {
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const [subtitles, setSubtitles] = useState<Subtitle[]>([initialSubtitle]);
    const { loadText, data, isLoading, error } = useFileLoader();
    const [failedMessage, setFailedMessage] = useState<string | null>(null);
    const [videoId, setVideoId] = useState<string | null>(null);

    useEffect(() => {
        if (!jobInfo) return;
        if (!jobInfo.source.url) {
            setFailedMessage("Invalid video ID");
            return;
        } else {
            setFailedMessage(null);
            setVideoId(new URL(jobInfo.source.url.value).searchParams.get("v"));
        }

        if (jobInfo.artifact_tags.Instrumental) {
            setAudioUrl(`/artifact/${jobInfo.artifact_tags.Instrumental.value}`);
        } else if (!jobInfo.isRunning()) {
            setFailedMessage('Conversion failed')
        }

        if (jobInfo.artifact_tags.subtitles) {
            loadText(`/artifact/${jobInfo.artifact_tags.subtitles.value}`);
        } else if (!jobInfo.isRunning()) {
            setSubtitles([failedSubtitle]);
        }
    }, [jobInfo]);

    
    useEffect(() => {
        if (error) {
            setSubtitles([failedSubtitle]);
        } else if (data)
            setSubtitles(JSON.parse(data));
    }, [data, error]);

    return {
        failedMessage,
        audioUrl, subtitles, videoId
    }
}