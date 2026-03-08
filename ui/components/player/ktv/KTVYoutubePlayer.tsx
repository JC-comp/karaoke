import React, { useEffect, useState, useRef } from "react";
import { Subtitle } from "@/types/subtitle";
import YoutubeEmbbedPlayer, { PlayerConfig } from "../YoutubeEmbbedPlayer";
import styles from './KTVYoutubePlayer.module.css'
import KTVSubtitle from "./KTVSubtitle";

interface KTVYoutubePlayerProps {
    videoId: string;
    audioUrl: string;
    subtitles: Subtitle[];
    config: PlayerConfig;
    handleStateChange?: (event: YT.OnStateChangeEvent) => void;
    handleInfoUpdate?: (data: Record<string, any>) => void;
}

export default function KTVYoutubePlayer({ videoId, audioUrl, subtitles, config, handleStateChange, handleInfoUpdate }: KTVYoutubePlayerProps) {
    const [currentTime, setCurrentTime] = useState(0);
    const audioRef = useRef<HTMLAudioElement>(null);
    const containerRef = React.useRef<HTMLDivElement>(null);
    function syncAudio(info: Record<string, any>) {
        const audio = audioRef.current;
        if (!audio) return;
        if (info.currentTime) {
            if (Math.abs(audio.currentTime - info.currentTime) > 0.5) {
                audio.currentTime = info.currentTime;
            }
        }
        if (info.volume)
            audio.volume = info.volume / 100;
    }
    function syncPlayer() {
        const audio = audioRef.current;
        if (!audio) return;
        if (!config.is_vocal_on && config.is_playing) {
            audio.play().catch((error) => {
                if (error.name === 'NotAllowedError') { }
            });
        } else {
            audio.pause();
        }
    }
    useEffect(() => {
        syncPlayer();
    }, [config]);

    function onInfoUpdate(info: Record<string, any>) {
        if (info.currentTime)
            setCurrentTime(info.currentTime);
        handleInfoUpdate?.(info);
        syncAudio(info);
    }

    return <div ref={containerRef} className={styles["ktv-player"]}>
        <audio ref={audioRef} className="d-none" controls src={audioUrl} />
        <YoutubeEmbbedPlayer
            videoId={videoId}
            config={config}
            handleStateChange={handleStateChange}
            handleInfoUpdate={onInfoUpdate} />
        <KTVSubtitle
            containerRef={containerRef}
            currentTime={currentTime}
            subtitles={subtitles} />
    </div>
}