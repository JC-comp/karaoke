"use client";

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner } from '@fortawesome/free-solid-svg-icons';
import WaveSurfer from "wavesurfer.js";
import ZoomPlugin from "wavesurfer.js/dist/plugins/zoom";
import WavesurferPlayer from '@wavesurfer/react'
import OverlapRegionsPlugin from "./SegmentViewerRegionPlugin";
import { useFetchArtifact } from "@/hooks/artifact/useFetchArtifact";
import './SegmentViewer.css';
import { useMemo } from 'react';

type Segment = {
  start: number;
  duration: number;
} | {
  start: number;
  end: number;
  text: string;
}

type Sentence = [{
  start: number;
  end: number;
  word: string;
}]
type ArtifactData = Segment[] | Sentence[];

interface SegmentRecord {
  "segment": string;
  "audio": string;
}

export default function SegmentViewer({ data, artifacts, isSentence }: { data: SegmentRecord, artifacts: Record<string, Artifact>, isSentence: boolean }) {
  const audioArtifact = artifacts?.[data.audio]
  const segmentArtifact = artifacts?.[data.segment]
  if (!audioArtifact || !segmentArtifact) {
    return <span className="text-muted">Artifact not found.</span>
  }

  const { isLoading: audioLoading, error: audioError, data: audioData } = useFetchArtifact(audioArtifact);
  const { isLoading: segmentLoading, error: segmentError, data: segmentData } = useFetchArtifact<ArtifactData>(segmentArtifact);
  const plugins = useMemo(
    () => [OverlapRegionsPlugin.create(), ZoomPlugin.create({ scale: 0.01 })], []);


  if (audioLoading || segmentLoading)
    return <div className="d-flex justify-content-center align-items-center m-auto flex-column">
      <FontAwesomeIcon icon={faSpinner} className="text-primary" spin />
      <span className="text-muted">Loading...</span>
    </div>;

  if (audioError || segmentError) {
    return <div className="d-flex justify-content-center align-items-center m-auto flex-column">
      <FontAwesomeIcon icon={faTimesCircle} className="text-danger" />
      <span className="text-danger">{audioError || segmentError}</span>
    </div>
  }

  if (segmentData == null || audioData == null) {
    return <div className="d-flex justify-content-center align-items-center m-auto flex-column">
      <FontAwesomeIcon icon={faTimesCircle} className="text-danger" />
      <span className="text-danger">Failed to load data</span>
    </div>
  }

  function parseSegment(segment: Segment) {
    const regionStart = segment.start;
    const regionEnd = ('end' in segment)
      ? segment.end
      : segment.start + segment.duration;
    const text = ('text' in segment) ? segment.text : undefined;
    return {
      regionStart, regionEnd, text
    }
  }

  function parseSentence(sentence: Sentence) {
    const regionStart = sentence[0].start;
    const regionEnd = sentence[sentence.length - 1].end;
    const text = sentence.map((wordObj, index) => {
      const isAscii = /^[\x00-\x7F]*$/.test(wordObj.word);
      if (isAscii && index !== 0) {
        return " " + wordObj.word;
      }
      return wordObj.word;
    }).join("");
    return {
      regionStart, regionEnd, text
    }
  }

  function addRegion(wavesurfer: WaveSurfer) {
    if (segmentData == null)
      return;
    const regionPlugin = plugins[0] as OverlapRegionsPlugin;
    regionPlugin.clearRegions();
    segmentData.forEach((segment, id) => {
      const { regionStart, regionEnd, text } = isSentence ? parseSentence(segment as Sentence) : parseSegment(segment as Segment);
      const content = text === undefined ? undefined : document.createElement('div');
      if (content) {
        if (text)
          content.innerText = text;
        content.style.zIndex = "6";
        content.addEventListener('click', (e) => {
          e.stopPropagation();
          wavesurfer.seekTo(regionStart / wavesurfer.getDuration());
        })
      }
      regionPlugin.addRegion({
        id: id.toString(),
        start: regionStart,
        end: regionEnd,
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

  return <WavesurferPlayer
    url={audioData}
    mediaControls
    plugins={plugins}
    onDecode={addRegion}
  />
}