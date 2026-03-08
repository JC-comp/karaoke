import { useYoutubeApi } from "@/hooks/player/useYoutubeApi";
import { useEffect, useRef } from "react"
import { toast, Id } from "react-toastify";
import styles from './YoutubeEmbbedPlayer.module.css'

export interface PlayerConfig {
    unmanaged: boolean;
    is_playing: boolean;
    is_vocal_on: boolean;
}

interface YoutubeEmbbedPlayerProps {
    videoId: string;
    config: PlayerConfig;
    handleStateChange?: (event: YT.OnStateChangeEvent) => void;
    handleInfoUpdate?: (data: Record<string, any>) => void;
}

export default function YoutubeEmbbedPlayer({ videoId, config, handleStateChange, handleInfoUpdate }: YoutubeEmbbedPlayerProps) {
    const apiReady = useYoutubeApi();
    const playerRef = useRef<YT.Player | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const toastIdRef = useRef<Id | null>(null);

    const callbacksRef = useRef({ onReady, onStateChange, onInfoUpdate });
    useEffect(() => {
        callbacksRef.current = { onReady, onStateChange, onInfoUpdate };
    });

    useEffect(() => {
        if (!apiReady || !containerRef.current) return;
        var player = new YT.Player(containerRef.current, {
            videoId: videoId,
            playerVars: {
                'playsinline': 1,
                'disablekb': 1,
                'fs': 0,
                'mute': 0,
            },
            events: {
                onReady: (e) => callbacksRef.current.onReady(e),
                onStateChange: (e) => callbacksRef.current.onStateChange(e),
            }
        });

        function onPlayerMessage(event: MessageEvent) {
            var data = JSON.parse(event.data);
            if (
                data.event === "infoDelivery" &&
                data.info
            ) {
                callbacksRef.current.onInfoUpdate(data.info);
            }
        }
        window.addEventListener('message', onPlayerMessage);

        return () => {
            if (playerRef.current) {
                playerRef.current = null;
                player.destroy();
            }
            window.removeEventListener('message', onPlayerMessage);
        }
    }, [videoId, containerRef, apiReady]);

    useEffect(() => {
        syncPlayer();
    }, [config]);

    useEffect(() => {
        const handleFocus = () => {
            window.removeEventListener('click', handleFocus);
            syncPlayer();
        };

        window.addEventListener('click', handleFocus);
        return () => {
            window.removeEventListener('click', handleFocus);
        };
    }, []);

    function syncPlayer() {
        const player = playerRef.current;
        if (!player) return;
        
        if (!config.unmanaged)
            config.is_playing ? player.playVideo() : player.pauseVideo();
        if (player.isMuted() != !config.is_vocal_on)
            config.is_vocal_on ? player.unMute() : player.mute();
    }

    function onReady(event: YT.PlayerEvent) {
        playerRef.current = event.target;
        syncPlayer();
    }

    function onStateChange(event: YT.OnStateChangeEvent) {
        handleStateChange?.(event);
        if (event.data == YT.PlayerState.UNSTARTED) {
            if (config.is_playing) {
                if (!toastIdRef.current) {
                    toastIdRef.current = toast.warn('Please interact with the page to start playback.', {
                        autoClose: false,
                        closeOnClick: false,
                    });
                }
            }
        } else if (toastIdRef.current) {
            toast.dismiss(toastIdRef.current);
            toastIdRef.current = null;
        }
        const isPlaying = event.data === YT.PlayerState.PLAYING;
        if (!config.unmanaged && isPlaying !== config.is_playing) {
            config.is_playing ? event.target.playVideo() : event.target.pauseVideo();
        }
    }

    function onInfoUpdate(data: Record<string, any>) {
        handleInfoUpdate?.(data);
    }

    return <div className={`${styles.container} h-100 w-100`}>
        <div ref={containerRef}></div>
    </div>
}