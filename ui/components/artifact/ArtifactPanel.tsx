import React, { useState } from 'react';
import { TaskInfo } from '@/models/TaskInfo';
import Artifact from './Artifact';
import styles from './ArtifactPanel.module.css';

export default function ArtifactPanel({ task, artifacts, visible }: { task: TaskInfo, artifacts: Record<string, Artifact>, visible: boolean }) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const detailRef = React.createRef<HTMLDetailsElement>();
  return <details ref={detailRef} onToggle={() => setDetailsOpen(detailRef.current?.open || false)}>
    <summary className="rounded">Task Artifacts</summary>
    {
      visible && detailsOpen && <table className={`table table-striped table-hover ${styles['artifact-table']}`}>
        <colgroup>
          <col span={1} style={{ width: '20%' }} />
          <col span={1} style={{ width: '80%' }} />
        </colgroup>
        <tbody>
          {
            Object.entries(task.artifacts).filter(([aid, artifact]) => artifact.attached).map(([aid, artifact]) => (
              <tr key={aid}>
                <td scope='row'>{artifact.name}</td>
                <td>
                  <div className='position-relative'>
                    <Artifact artifact={artifact} artifacts={artifacts} />
                  </div>
                </td>
              </tr>
            ))
          }
        </tbody>
      </table>
    }
  </details>

}
