import { useEffect, useState, useRef } from "react"
import { toast, Id } from "react-toastify";

declare global {
    interface Window {
        onYouTubeIframeAPIReady: (() => void) | undefined;
    }
}

interface YoutubeEmbbedPlayerProps {
    videoId: string;
    shouldPlay: boolean;
    onPlayerReady?: (event: YT.PlayerEvent) => void;
    onPlayerStateChange?: (event: YT.OnStateChangeEvent) => void;
    onStateChange?: (player: YT.Player) => void;
    onInfoUpdate?: (info: Record<string, any>) => void;
}

export default function YoutubeEmbbedPlayer({ videoId, shouldPlay, onPlayerReady, onPlayerStateChange, onStateChange, onInfoUpdate }: YoutubeEmbbedPlayerProps) {
    const [apiReady, setApiReady] = useState(false);
    const [checkInteracted, setCheckInteracted] = useState<Id | null>(null);
    const playerRef = useRef<YT.Player | null>(null);

    useEffect(() => {
        var tag = document.createElement('script');

        tag.src = "https://www.youtube.com/iframe_api";
        document.body.appendChild(tag);
        function onYouTubeIframeAPIReady() {
            setApiReady(true);
        }
        window.onYouTubeIframeAPIReady = onYouTubeIframeAPIReady;
        if (window.YT && window.YT.Player) {
            setApiReady(true);
        }

        return () => {
            window.onYouTubeIframeAPIReady = undefined;
            if (tag) {
                tag.remove();
            }
        }
    }, []);

    useEffect(() => {
        if (!shouldPlay) return;
        const checkInterval = setInterval(() => {
            const player = playerRef.current;
            if (!player) return;
            if (player.getPlayerState() === YT.PlayerState.PLAYING) {
                clearInterval(checkInterval);
                if (checkInteracted) {
                    setCheckInteracted(null);
                    toast.dismiss(checkInteracted);
                }
                return;
            }
            if (!checkInteracted) {
                const toastId = toast.warn('Please interact with the page to start playback.', {
                    autoClose: false,
                    closeOnClick: false,
                });
                setCheckInteracted(toastId);
            }
            player.playVideo();
        }, 1000);
        return () => {
            console.log("clearing interval");
            clearInterval(checkInterval);
            if (checkInteracted) {
                setCheckInteracted(null);
                toast.dismiss(checkInteracted);
            }
        }
    }, [checkInteracted, shouldPlay]);

    function onYoutubePlayerReady(event: YT.PlayerEvent) {
        event.target.unMute();
        if (onPlayerReady) onPlayerReady(event);
    }

    useEffect(() => {
        if (!apiReady) return;
        var player = new YT.Player('player', {
            videoId: videoId,
            playerVars: {
                'playsinline': 1,
                'disablekb': 1,
                'fs': 0,
                'mute': 0,
            },
            events: {
                'onReady': onYoutubePlayerReady,
                'onStateChange': onPlayerStateChange
            }
        });
        playerRef.current = player;

        var iframeWindow = player.getIframe().contentWindow;
        function onPlayerMessage(event: MessageEvent) {
            if (event.source !== iframeWindow)
                return;
            var data = JSON.parse(event.data);
            if (
                data.event === "infoDelivery" &&
                data.info
            ) {
                if (onInfoUpdate)
                    onInfoUpdate(data.info);
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

    }, [videoId, apiReady]);

    useEffect(() => {
        if (!onStateChange)
            return;

        const player = playerRef.current;
        if (!player || !player.playVideo) return;
        onStateChange(player);
    });

    return <div className="h-100 w-100">
        <div id="player"></div>
    </div>
}