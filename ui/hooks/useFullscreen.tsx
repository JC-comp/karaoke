import React, { useState, useEffect } from 'react';

export default function useFullscreen(ref: React.RefObject<HTMLElement | null>) {
    const [isFullscreen, setIsFullscreen] = useState(false);

    useEffect(() => {
        const handler = () => setIsFullscreen(!!document.fullscreenElement);
        document.addEventListener('fullscreenchange', handler);
        return () => document.removeEventListener('fullscreenchange', handler);
    }, []);

    const toggle = () => {
        if (!document.fullscreenElement) {
            ref.current?.requestFullscreen().catch(console.error);
        } else {
            document.exitFullscreen();
        }
    };

    return { isFullscreen, toggle };
}