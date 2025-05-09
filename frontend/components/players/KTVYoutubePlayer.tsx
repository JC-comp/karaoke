import React, { use, useEffect, useState } from "react";
import { toast, Id } from "react-toastify";
import YoutubeEmbbedPlayer from './YoutubeEmbbedPlayer';

interface KTVYoutubePlayerProps {
    videoId: string;
    shouldPlay: boolean;
    audioUrl: string;
    subtitles: Subtitle[];
    onPlayerReady?: (event: YT.PlayerEvent) => void;
    onPlayerStateChange?: (event: YT.OnStateChangeEvent) => void;
    onStateChange?: (player: YT.Player) => void;
    onInfoUpdate?: (info: Record<string, any>) => void;
}

export default function KTVYoutubePlayer({ videoId, shouldPlay, audioUrl, subtitles, onPlayerReady, onPlayerStateChange, onStateChange, onInfoUpdate }: KTVYoutubePlayerProps) {
    const [showingSubtitles, setShowingSubtitles] = useState<Subtitle[]>(subtitles);
    const [currentTime, setCurrentTime] = useState(0);
    const videoRef = React.useRef<YT.Player | null>(null);
    const audioRef = React.useRef<HTMLAudioElement>(null);
    const containerRef = React.useRef<HTMLDivElement>(null);

    function onKTVPlayerReady(event: YT.PlayerEvent) {
        const player = event.target;
        videoRef.current = player;
        if (onPlayerReady) onPlayerReady(event);
    }

    function onKTVPlayerStateChange(event: YT.OnStateChangeEvent) {
        if (onPlayerStateChange) onPlayerStateChange(event);
        const audio = audioRef.current;
        if (!audio) return;
        if (event.data === YT.PlayerState.PLAYING) {
            audio.play().then(() => {
                videoRef.current?.mute();
            }).catch((error) => {
                if (error.name === 'NotAllowedError') {
                    
                }
            });
        } else if (event.data === YT.PlayerState.PAUSED) {
            audio.pause();
        }
    }

    function onKTVInfoUpdate(info: Record<string, any>) {
        if (onInfoUpdate) onInfoUpdate(info);
        const audio = audioRef.current;
        if (audio) {
            if (info.currentTime) {
                if (Math.abs(audio.currentTime - info.currentTime) > 0.5)
                    audio.currentTime = info.currentTime;
                setCurrentTime(info.currentTime);
            }
            if (info.volume)
                audio.volume = info.volume / 100;
            if (info.muted !== undefined)
                audio.muted = !info.muted;
        }
    }

    function getSubtitleStyle(args: Partial<Subtitle>) {
        const container = containerRef.current;
        if (!container) return;
        const width = container.clientWidth;
        const height = container.clientHeight;
        const { font_size, x, y, alignX, alignY, bottom } = args;
        var result = {} as Record<string, string>;
        if (font_size) {
            result.fontSize = (font_size * width) + 'px';
        }
        if (alignX === 'center') {
            result.left = '50%';
            result.transform = 'translateX(-50%)';
        } else if (alignX === 'left') {
            if (x)
                result.left = ((x || 0) * width) + 'px';
        } else if (alignX === 'right') {
            if (x)
                result.right = ((1 - (x || 0)) * width) + 'px';
        }
        
        let marginBottom = 0;
        if (height > width) {
            marginBottom = height / 4;
        }

        if (alignY === 'top') {
            if (y)
                result.top = ((y || 0) * width - marginBottom) + 'px';
        } else if (alignY === 'bottom') {
            if (y)
                result.bottom = ((y || 0) * width + marginBottom) + 'px';
        } else if (alignY === 'center') {
            result.top = ((height - (bottom || 0) * width) / 2 + (y || 0) * width - marginBottom) + 'px';
        }
        return result;
    }

    useEffect(() => {
        const preAnimTime = currentTime + 0.5;
        var result = subtitles.filter((subtitle) => {
            return preAnimTime >= subtitle.start && preAnimTime <= subtitle.end;
        })
        setShowingSubtitles(result);
        const container = containerRef.current;
        if (!container) return;
        const wordElements = container.querySelectorAll('.word');
        for (let i = 0; i < wordElements.length; i++) {
            const wordElement = wordElements[i] as HTMLElement;
            const fg = wordElement.querySelector('.fg') as HTMLElement;
            const start = parseFloat(wordElement.dataset.start || '0');
            const end = parseFloat(wordElement.dataset.end || '0');
            const duration = end - start;
            const offset = Math.max(0, preAnimTime - start);
            const percent = Math.max(0, Math.min(1, offset / duration));
            fg.style.width = (percent * 100) + '%';
        }
    }, [currentTime, subtitles]);

    useEffect(() => {
        function onResize() {
            const container = containerRef.current;
            if (!container) return;
            const subtitleElements = container.querySelectorAll('.subtitle');
            for (let i = 0; i < subtitleElements.length; i++) {
                const subtitleElement = subtitleElements[i] as HTMLElement;
                const fontSize = subtitleElement.dataset.fontSize;
                const x = subtitleElement.dataset.x;
                const y = subtitleElement.dataset.y;
                const bottom = subtitleElement.dataset.bottom;
                const alignX = subtitleElement.dataset.alignX;
                const alignY = subtitleElement.dataset.alignY;
                const styles = getSubtitleStyle({
                    font_size: fontSize ? parseFloat(fontSize) : undefined,
                    x: x ? parseFloat(x) : undefined,
                    y: y ? parseFloat(y) : undefined,
                    bottom: bottom ? parseFloat(bottom) : undefined,
                    alignX: alignX,
                    alignY: alignY,
                });
                for (const key in styles) {
                    // split key by camelCase
                    const newKey = key.replace(/([a-z])([A-Z])/g, '$1-$2').toLowerCase();
                    subtitleElement.style.setProperty(newKey, styles[key] as string);
                }
            }
        }
        window.addEventListener('resize', onResize);
        onResize();
        return () => {
            window.removeEventListener('resize', onResize);
        }
    }, []);

    function onKTVStateChange(player: YT.Player) {
        if (onStateChange) onStateChange(player);
    }

    return (
        <div ref={containerRef} className="ktv-player">
            {
                audioUrl && <audio
                    ref={audioRef} className="d-none" controls src={audioUrl}
                />
            }
            <YoutubeEmbbedPlayer
                videoId={videoId}
                shouldPlay={shouldPlay}
                onPlayerReady={onKTVPlayerReady}
                onStateChange={onKTVStateChange}
                onInfoUpdate={onKTVInfoUpdate}
                onPlayerStateChange={onKTVPlayerStateChange} />
            {
                showingSubtitles.map((subtitle, index) =>
                    <div
                        className="subtitle"
                        key={subtitle.x + ':' + subtitle.y + ':' + subtitle.start}
                        style={getSubtitleStyle(subtitle)}
                        data-align-x={subtitle.alignX}
                        data-align-y={subtitle.alignY}
                        data-x={subtitle.x}
                        data-y={subtitle.y}
                        data-bottom={subtitle.bottom}
                        data-font-size={subtitle.font_size}
                    >
                        {
                            subtitle.words.map((word, index) =>
                                <div
                                    className="word"
                                    key={index}
                                    data-start={word.start}
                                    data-end={word.end}
                                >
                                    <span className="bg">{word.word}</span>
                                    <span className="fg" style={{width: 0}}>{word.word}</span>
                                </div>
                            )
                        }
                    </div>
                )
            }
        </div>
    )
}