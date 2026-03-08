import { useState, useEffect } from 'react';

let apiState: 'loading' | 'ready' = 'loading';
let subscribers: Array<() => void> = [];

declare global {
    interface Window {
        onYouTubeIframeAPIReady: (() => void) | undefined;
    }
}
export const useYoutubeApi = () => {
    const [isReady, setIsReady] = useState(apiState === 'ready');

    useEffect(() => {
        if (apiState === 'ready') {
            setIsReady(true);
            return;
        }

        const handleReady = () => setIsReady(true);
        subscribers.push(handleReady);

        if (window.YT && window.YT.Player) {
            apiState = 'ready';
            subscribers.forEach((cb) => cb());
            subscribers = [];
            return;
        }

        if (!document.getElementById('youtube-iframe-api')) {
            const tag = document.createElement('script');
            tag.id = 'youtube-iframe-api';
            tag.src = "https://www.youtube.com/iframe_api";
            document.body.appendChild(tag);

            window.onYouTubeIframeAPIReady = () => {
                apiState = 'ready';
                subscribers.forEach((cb) => cb());
                subscribers = [];
            };
        }
    }, []);

    return isReady;
};