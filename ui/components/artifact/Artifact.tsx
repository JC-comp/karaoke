'use client'

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner } from '@fortawesome/free-solid-svg-icons';
import { useFetchArtifact } from "@/hooks/artifact/useFetchArtifact"
import dynamic from 'next/dynamic';
import PlainViewer from './viewer/PlainViewer';
import { useTheme } from '@/contexts/theme/ThemeContext';
import WavesurferPlayer from '@wavesurfer/react'
import ZoomPlugin from "wavesurfer.js/dist/plugins/zoom";
import SegmentViewer from './viewer/SegmentViewer';
import { useMemo } from 'react';

const DynamicReactJson = dynamic(() => import('@microlink/react-json-view'), { ssr: false });

export default function Artifact({ artifact, artifacts }: { artifact: Artifact, artifacts: Record<string, Artifact> }) {
    const { isLoading, error, data } = useFetchArtifact(artifact)
    const { theme } = useTheme();
    const zoomPlugin = useMemo(() => [
        ZoomPlugin.create({ scale: 0.01 })
    ], []);

    if (isLoading) {
        return <div className="d-flex justify-content-center align-items-center m-auto flex-column">
            <FontAwesomeIcon icon={faSpinner} className="text-primary" spin />
            <span className="text-muted">Loading...</span>
        </div>
    }
    if (error) {
        return <div className="d-flex justify-content-center align-items-center m-auto flex-column">
            <FontAwesomeIcon icon={faTimesCircle} className="text-danger" />
            <span className="text-danger">{error}</span>
        </div>
    }
    switch (artifact.type) {
        case 'audio':
            return <div>
                <WavesurferPlayer
                    url={data}
                    mediaControls
                    plugins={zoomPlugin}
                />
            </div>
        case 'segment':
            return <SegmentViewer data={data} artifacts={artifacts} isSentence={false} />
        case 'sentence':
            return <SegmentViewer data={data} artifacts={artifacts} isSentence={true} />
        case 'json':
            return <DynamicReactJson src={data} theme={theme == 'dark' ? 'ashes' : 'rjv-default'} />
        case 'text':
            return <PlainViewer data={data} />
        default:
            return <span className="text-muted">Preview type {artifact.type} not available</span>
    }
}
