import { useEffect, useState, useRef } from "react"
import KareokeRoomModel from '@/models/ktv';

declare global {
    interface Window {
        onYouTubeIframeAPIReady: (() => void) | undefined;
    }
}

export default function YoutubeEmbbedPlayer({ kareokeRoomModel, videoId }: { kareokeRoomModel: KareokeRoomModel | null; videoId: string }) {
    const [apiReady, setApiReady] = useState(false);
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
        if (!apiReady) return;
        var player = new YT.Player('player', {
            videoId: videoId,
            playerVars: {
                'playsinline': 1
            },
            events: {
                'onReady': onPlayerReady,
                'onStateChange': onPlayerStateChange
            }
        });
        playerRef.current = player;

        function onPlayerReady(event: YT.PlayerEvent) {
            if (kareokeRoomModel?.is_playing)
                event.target.playVideo();
        }

        function onPlayerStateChange(event: YT.OnStateChangeEvent) {
            if (event.data == YT.PlayerState.ENDED) {
                kareokeRoomModel?.moveToNextItem();
            }
        }

        return () => {
            if (playerRef.current) {
                playerRef.current = null;
                player.destroy();
            }
        }

    }, [videoId, apiReady]);

    useEffect(() => {
        if (!kareokeRoomModel) return;
        const player = playerRef.current;
        if (!player || !player.playVideo) return;
        if (kareokeRoomModel.is_playing) {
            player.playVideo();
        }
        else
            player.pauseVideo();

    });
    return <div id="player-container">
        <div id="player"></div>
    </div>
}