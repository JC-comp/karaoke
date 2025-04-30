import React, { useState, useEffect } from 'react';
import Link from 'next/link';

import { getStatusIcon } from '@/utils/icon';
import connectSocketIO from "@/utils/socketio";
import { JobInfo } from '@/models/job';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';
export default function FileJobTab() {
  const [jobs, setJobs] = useState<{ [key: string]: JobInfo }>({});
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const preJoin = () => {
      setIsLoading(true);
      setError(null);
    }
    const onError = (error: string) => {
      setError(error);
      setIsLoading(false);
    }
    const { socket, unsubscribe } = connectSocketIO('/job', '*', preJoin, onError);
    socket.on('progress', (parsedData) => {
      const job = JobInfo.fromJSON(parsedData);
      setJobs((prevJobs) => ({ ...prevJobs, [job.jid]: job }));
      setIsLoading(false);
    });
    return () => {
      unsubscribe();
    }
  }, []);

  if (error) {
    return (<div className="alert alert-danger w-100" role="alert">
      {error}
    </div>)
  }

  return (
    <div>
      {
        isLoading ? (
          <div className="d-flex justify-content-center align-items-center my-2">
            <FontAwesomeIcon icon={faSpinner} spin size="2x" />
          </div>
        ) : Object.keys(jobs).length === 0 && (
          <div className="alert alert-info w-100" role="alert">
            No jobs found.
          </div>
        )
      }

      <table className="table table-striped table-hover text-center" style={{ tableLayout: 'fixed' }}>
        <tbody>
          {
            Object.values(jobs).map((job) => (
              <tr key={job.jid}>
                <td>
                  <div className='d-flex align-items-center'>
                    <span title={job.status} className='p-2'>
                      {getStatusIcon(job.status)}
                    </span>
                    <Link className='text-decoration-none overflow-hidden' href={`/job?jobId=${job.jid}`}>
                      <div className='text-truncate'>
                        {job.media.metadata.title || job.jid}
                      </div>
                    </Link>
                  </div>
                </td>
              </tr>
            ))
          }
        </tbody>
      </table>
    </div>
  )
}