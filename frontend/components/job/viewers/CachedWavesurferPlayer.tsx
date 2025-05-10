import { useEffect, useState } from "react";
import { type GenericPlugin } from 'wavesurfer.js/dist/base-plugin.js';
import WavesurferPlayer from '@wavesurfer/react'
import WaveSurfer from "wavesurfer.js";

export default function CachedWavesurferPlayer({ url, plugins, onDecode, setIsLoading, setError }: { url: string | null, plugins: GenericPlugin[], onDecode?: (wavesurfer: WaveSurfer) => void, setIsLoading: (loading: boolean) => void, setError: (error: string | null) => void }) {
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    useEffect(() => {
        if (audioUrl) return;
        if (!url) return;
        setError(null);
        setIsLoading(true);
        const controller = new AbortController();
        fetch(url, { signal: controller.signal })
            .then((response) => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.blob();
            }).then((blob) => {
                setAudioUrl(URL.createObjectURL(blob));
                setIsLoading(false);
            })
            .catch((error) => {
                if (error.name === 'AbortError') {
                    console.log('Fetch aborted');
                    return;
                }
                setError('Failed to load audio: ' + error.message);
            })
        return () => {
            controller.abort();
        }
    }, [url]);


    return audioUrl && <WavesurferPlayer
        url={audioUrl}
        mediaControls
        plugins={plugins}
        onDecode={(wavesurfer) => {
            if (onDecode) {
                onDecode(wavesurfer);
            }
        }}
        onError={() => setError('Failed to load audio')}
    />
}
