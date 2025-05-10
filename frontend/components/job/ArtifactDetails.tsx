import React, { useState, useEffect } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner } from '@fortawesome/free-solid-svg-icons';
import CachedWavesurferPlayer from "./viewers/CachedWavesurferPlayer";
import ZoomPlugin from "wavesurfer.js/dist/plugins/zoom";

import { JsonViewer, PlainViewer, SegmentViewer } from './viewers';

function ArtifactComponent( { artifact, jobId, setIsLoading, setError }: { artifact: Artifact; jobId: string; setIsLoading: (isLoading: boolean) => void; setError: (error: string | null) => void } ) {
  const url = `/api/artifact/${jobId}/${artifact.aid}`;
  switch (artifact.artifact_type) {
    case 'video':
      return <video controls className="w-100" 
      onLoadedData={() => setIsLoading(false)}
      onError={() => setError('Failed to load video')}
      >
        <source src={url} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    case 'audio':
      return <div><CachedWavesurferPlayer
        url={url}
        plugins={[ZoomPlugin.create({ scale: 0.01 })]}
        setIsLoading={setIsLoading}
        setError={setError}
      /></div>
    case 'json':
      return <JsonViewer url={url} setIsLoading={setIsLoading} setError={setError} />
    case 'text':
      return <PlainViewer url={url} setIsLoading={setIsLoading} setError={setError} />
    case 'segments':
      return <SegmentViewer url={url} jobId={jobId} setIsLoading={setIsLoading} setError={setError} />
    default:
      setIsLoading(false);
      return <span className="text-muted">Preview not available</span>
  }
}

function Artifact({ artifact, jobId }: { artifact: Artifact; jobId: string }) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  return <tr key={artifact.aid}>
    <td scope='row'>{artifact.name}</td>
    <td>
      <div className='position-relative'>
        {
          !error && <ArtifactComponent artifact={artifact} jobId={jobId} setIsLoading={setIsLoading} setError={setError} />
        }
        {
          !error && isLoading && <div className="d-flex justify-content-center align-items-center m-auto flex-column position-absolute h-100 w-100 top-0 start-0 z-2">
            <FontAwesomeIcon icon={faSpinner} className="text-primary" spin />
            <span className="text-muted">Loading...</span>
          </div>
        }
        {
          error && <div className="d-flex justify-content-center align-items-center m-auto flex-column">
            <FontAwesomeIcon icon={faTimesCircle} className="text-danger" />
            <span className="text-danger">{error}</span>
          </div>
        }
      </div>
    </td>
  </tr>
}

export default function ArtifactDetails({ task, jobId }: { task: Task; jobId: string }) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const detailRef = React.createRef<HTMLDetailsElement>();
  return <details ref={detailRef} className="log-details" onToggle={() => setDetailsOpen(detailRef.current?.open || false)}>
    <summary className="rounded">Task Artifacts</summary>
    {
      detailsOpen && <table className="table table-striped table-hover artifact-table">
        <colgroup>
          <col span={1} style={{ width: '20%' }} />
          <col span={1} style={{ width: '80%' }} />
        </colgroup>
        <tbody>
          {
            task.artifacts.filter(artifact => !artifact.is_attached).map((artifact) => (
              <Artifact key={artifact.aid} artifact={artifact} jobId={jobId} />
            ))
          }
        </tbody>
      </table>
    }
  </details>

}