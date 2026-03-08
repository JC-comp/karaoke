import React, { use, useEffect, useState } from "react";
import { Subtitle } from "@/types/subtitle";
import styles from './KTVSubtitle.module.css'

interface KTVSubtitleProps {
    currentTime: number;
    subtitles: Subtitle[];
    containerRef: React.RefObject<HTMLDivElement | null>;
}

interface IndexedSubtitle extends Subtitle {
    index: number;
}

export default function KTVSubtitle({ currentTime, subtitles, containerRef }: KTVSubtitleProps) {
    const indexdSubtitles = subtitles.map((subtitle, index) => ({ ...subtitle, index }));
    const [showingSubtitles, setShowingSubtitles] = useState<IndexedSubtitle[]>(indexdSubtitles);
    useEffect(() => {
        const preAnimTime = currentTime + 0.5;
        var result = indexdSubtitles.filter((subtitle) => {
            return preAnimTime >= subtitle.start && preAnimTime <= subtitle.end;
        })
        setShowingSubtitles(result);
    }, [currentTime, subtitles]);

    function getWordWidth(start: number, end: number) {
        const progressTime = currentTime + 0.5;
        const duration = end - start || 0.1;
        const offset = Math.max(0, progressTime - start);
        const percent = Math.max(0, Math.min(1, offset / duration));
        return percent * 100;
    }

    function getSubtitleStyle(args: Partial<Subtitle>) {
        const container = containerRef.current;
        if (!container) return;
        const width = container.clientWidth;
        const height = container.clientHeight;
        const { font_size, x, y, alignX, alignY, bottom } = args;
        var result = {} as Record<string, string>;
        if (font_size) {
            result.fontSize = (font_size * width / 1.5) + 'px';
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

        let marginBottom = 30;
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
    
    return showingSubtitles.map((subtitle, index) =>
        <div
            className={styles.subtitle}
            key={`${subtitle.index}-${subtitle.start}-${subtitle.end}`}
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
                        className={styles.word}
                        key={`${index}-${word.start}-${word.end}`}
                        data-start={word.start}
                        data-end={word.end}
                    >
                        <span className={styles.bg}>{word.text}</span>
                        <span className={styles.fg} style={{ width: `${getWordWidth(word.start, word.end)}%` }}>{word.text}</span>
                    </div>
                )
            }
        </div>
    )

}