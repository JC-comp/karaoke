"use client";

import { useEffect, useState } from "react";
import WavesurferPlayer from '@wavesurfer/react'
import { type GenericPlugin } from 'wavesurfer.js/dist/base-plugin.js';
import WaveSurfer from "wavesurfer.js";
import ZoomPlugin from "wavesurfer.js/dist/plugins/zoom";
import OverlapRegionsPlugin from "./SegmentViewerRegionPlugin";
import { useFetchArtifact } from "@/utils/artifact";

import './SegmentViewer.css';

interface Segment {
  original_start: number;
  original_end: number;
  start: number;
  end: number;
  text: string;
  word: string;
}

export default function SegmentViewer({ url, jobId, setIsLoading, setError }: { url: string, jobId: string, setIsLoading: (loading: boolean) => void, setError: (error: string) => void }) {
  const rawData = useFetchArtifact(url, setError);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [plugins, setPlugins] = useState<GenericPlugin[]>([
    OverlapRegionsPlugin.create(), ZoomPlugin.create({ scale: 0.01 })
  ]);
  
  useEffect(() => {
    if (!rawData)
      return
    const body = JSON.parse(rawData);
    setSegments(body['segments']);
    setAudioUrl(`/api/artifact/${jobId}/file/${body['audio']}`)
  }, [rawData]);

  function addRegion(wavesurfer: WaveSurfer) {
    const regionPlugin = plugins[0] as OverlapRegionsPlugin;
    regionPlugin.clearRegions();
    segments.forEach((segment, id) => {
      const regionStart = segment.original_start === undefined ? segment.start : segment.original_start;
      const text = segment.text || segment.word;
      const content = text === undefined ? undefined : document.createElement('div');
      if (content) {
        content.innerText = segment.text || segment.word;
        content.style.zIndex = "6";
        content.addEventListener('click', (e) => {
          e.stopPropagation();
          wavesurfer.seekTo(regionStart / wavesurfer.getDuration());
        })
      }
      regionPlugin.addRegion({
        id: id.toString(),
        start: regionStart,
        end: segment.original_end === undefined ? segment.end : segment.original_end,
        content: content,
        drag: false,
        resize: false,
      })
      
    })
    regionPlugin.on('region-in', (region) => {
      region.setOptions({ color: 'rgba(0, 0, 0, 0.4)' })
      if (region.content) {
        region.content.style.color = 'var(--bs-primary-text-emphasis)';
        region.content.style.backgroundColor = 'rgba(0, 0, 0, 0.4)';
        region.content.style.fontWeight = 'bold';
      }
    })
    regionPlugin.on('region-out', (region) => {
      region.setOptions({ color: 'rgba(0, 0, 0, 0.1)' })
      if (region.content) {
        region.content.style.color = '';
        region.content.style.backgroundColor = '';
        region.content.style.fontWeight = '';
      }
    })
  }

  return audioUrl && <div>
    <div>
      <WavesurferPlayer
        url={audioUrl}
        mediaControls
        plugins={plugins}
        onDecode={addRegion}
        onReady={() => setIsLoading(false)}
        onError={() => setError('Failed to load audio')}
      />
    </div>
  </div>
}