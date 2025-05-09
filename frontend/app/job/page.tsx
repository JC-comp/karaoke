'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useSearchParams } from 'next/navigation'
import Moment from 'react-moment';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner, faPaperclip, IconDefinition } from '@fortawesome/free-solid-svg-icons';
import { toast } from 'react-toastify';

import ArtifactDetails from '@/components/job/ArtifactDetails';
import ProductPreview from '@/components/job/ProductPreview';
import { JobInfo } from '@/models/job';
import connectSocketIO from "@/utils/socketio";
import { getStatusColor, getStatusIcon } from '@/utils/icon';
import { timeDiff, timeDiffSec } from '@/utils/time';
import { capitalizeFirstLetter } from '@/utils/job';

import styles from './page.module.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import '@/components/job/ProductPreview.css';
import '@/components/job/ArtifactDetails.css';
import '@/components/players/KTVYoutubePlayer.css';



function usePrevious(value: JobInfo | null) {
  const ref = useRef<JobInfo | null>(null);
  useEffect(() => {
    ref.current = value;
  });
  return ref.current;
}

function parseLogLines(log: string) {
  const lines = log.split('\n');
  const re = /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\d+) - ([^ ]+) - ([^ ]+) - (.*)$/s;

  const parsedLines = lines.reduce((filtered, line) => {
    const match = line.match(re);
    if (match) {
      const timestamp = match[1].replace(',', '.');
      const pid = match[2];
      const module = match[3];
      const level = match[4];
      const message = match[5].split('\r').reverse()[0];
      filtered.push({
        'timestamp': timestamp,
        'pid': pid,
        'module': module,
        'level': level,
        'message': message,
      });
    }
    return filtered;
  }, [] as LogLine[]);

  return parsedLines.map((line, index) => (
    <div key={index} className={`d-flex flex-row ${styles['log-line']}`}>
      <code className={styles['log-line-number']}>{index + 1}</code>
      <code>
        <span className='user-select-none' title={line.timestamp}>{timeDiff(parsedLines[0].timestamp, line.timestamp)}</span>
        <span className='user-select-none'>[{line.level}]</span>
        <span style={{ whiteSpace: 'pre-wrap' }}>{line.message}</span>
      </code>
    </div>
  ))
}

function resetDetails(e: React.MouseEvent<HTMLButtonElement>) {
  const details = window.document.querySelectorAll('details');
  details.forEach((element) => {
    if (element.open) {
      element.removeAttribute('open');
    }
  });
}

const JobProcessPage = () => {
  const router = useRouter()
  const searchParams = useSearchParams();
  const jobId = searchParams.get('jobId');
  const [jobInfo, setJobInfo] = useState<JobInfo | null>(null);
  const prevJobInfo = usePrevious(jobInfo);
  const [failedMessage, setFailedMessage] = useState<string | null>(null);

  if (!jobId) {
    toast.error('Job ID is missing');
    router.push('/');
    return;
  }

  useEffect(() => {
    if (!jobInfo) return;
    if (prevJobInfo && prevJobInfo.status !== jobInfo.status)
      toast.info(`Job status changed to ${jobInfo.status}`);
  }, [jobInfo]);

  useEffect(() => {
    const onError = (error: string) => {
      setFailedMessage(error);
      setJobInfo(null);
    }

    const preJoin = () => {
      setFailedMessage(null);
      setJobInfo(null);
    }

    const { socket, unsubscribe } = connectSocketIO('/job', jobId, preJoin, onError);

    socket.on('progress', (parsedData) => {
      setFailedMessage(null);
      setJobInfo(JobInfo.fromJSON(parsedData));
    });

    return () => {
      unsubscribe();
    }
  }, [jobId]);

  const goBackOrHome = () => {
    if (window.history.state.key) {
      router.back();
    } else {
      router.push('/');
    }
  }

  function processingHint(message: string, textColor: string, spin: boolean, icon: IconDefinition) {
    return (
      <div className="root flex-column text-center">
        <FontAwesomeIcon icon={icon} className={`${textColor} mb-3`} size="3x" spin={spin} />
        <p className="lead">{message}</p>
        <p className="mt-3">Job ID: {jobId}</p>
        <button className="btn btn-outline-info btn-lg" onClick={goBackOrHome}>
          Back
        </button>
      </div>
    )
  }

  if (failedMessage) {
    return processingHint(failedMessage, 'text-danger', false, faTimesCircle);
  }

  if (jobInfo == null) {
    return processingHint('Loading job information...', '', true, faSpinner);
  }

  return (
    <div className="container-fluid d-flex flex-column h-100 p-3">
      <div className="d-flex flex-row justify-content-between align-items-center mb-3">
        <button className="btn btn-outline-info btn-lg" onClick={goBackOrHome}>
          Back
        </button>
        <span className="text-start flex-grow-1 px-3">Job: {jobId}</span>
      </div>
      <div className={`${styles["progress-row"]}`}>
        <div className="col-md-4 overflow-auto">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Job Information</h5>
              <ul className='list-group list-group-flush'>
                <li className="list-group-item">
                  <strong>Created At:</strong> <Moment fromNow withTitle date={jobInfo.created_at * 1000} />
                </li>
                {
                  jobInfo.started_at && (
                    <li className="list-group-item">
                      <strong>Queued: </strong>
                      {timeDiffSec(jobInfo.started_at, jobInfo.created_at)}
                    </li>
                  )
                }
                {
                  jobInfo.started_at && jobInfo.finished_at && (
                    <li className="list-group-item">
                      <strong>Duration: </strong>
                      {timeDiffSec(jobInfo.started_at, jobInfo.finished_at)}
                    </li>
                  )
                }
                <li className="list-group-item">
                  <strong>Status:</strong> {getStatusIcon(jobInfo.status)} {capitalizeFirstLetter(jobInfo.status)}
                </li>
                {
                  <li className="list-group-item">
                    <strong>Result:</strong>
                    <div className="position-relative">
                      <ProductPreview jobInfo={jobInfo} />
                    </div>
                  </li>
                }
              </ul>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Media Metadata</h5>
              <ul className='list-group list-group-flush'>
                <li className="list-group-item">
                  <strong>ID:</strong> {jobInfo.media.metadata.id}
                </li>
                <li className="list-group-item">
                  <strong>Source:</strong> {jobInfo.media.source}
                </li>
                <li className="list-group-item">
                  <strong>Title:</strong> {jobInfo.media.metadata.title}
                </li>
                <li className="list-group-item">
                  <strong>Channel:</strong> {jobInfo.media.metadata.channel}
                </li>
                <li className="list-group-item">
                  <strong>Duration:</strong> {
                    jobInfo.media.metadata.duration ? jobInfo.media.metadata.duration + ' seconds'
                      : ''
                  }
                </li>
              </ul>
            </div>
          </div>
        </div>
        <div className="col-md-8 overflow-auto">
          {
            Object.keys(jobInfo.tasks).length > 0 ? (
              <div className={"accordion"} id="accordionTasks">
                {
                  Object.values(jobInfo.tasks).map((task) => (
                    <div className="accordion-item" key={task.tid}>
                      <div className="accordion-header" id={`heading${task.tid}`}>
                        <button className="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target={`#collapse${task.tid}`} aria-expanded="false" aria-controls={`collapse${task.tid}`} onClick={resetDetails}>
                          {getStatusIcon(task.status)}
                          <span className={`${styles["status-text"]} badge ${getStatusColor(task.status)} flex-shrink-0`}>
                            {capitalizeFirstLetter(task.status)}
                          </span>
                          <div className='d-flex flex-column overflow-hidden'>
                            <span>
                              {
                                task.hasArtifact() && (
                                  <FontAwesomeIcon icon={faPaperclip} className="me-2" />
                                )
                              }
                              {task.name}
                            </span>
                            <span className="text-truncate badge bg-secondary mw-100" title={task.message} style={{ marginInlineEnd: 'auto', whiteSpace: 'pre' }}>{task.message}</span>
                          </div>
                        </button>
                      </div>
                      <div id={`collapse${task.tid}`} className="accordion-collapse collapse" aria-labelledby={`heading${task.tid}`} data-bs-parent="#accordionTasks">
                        <div className={"accordion-body"}>
                          <div className='d-flex flex-column'>
                            {
                              task.hasArtifact() &&
                              <ArtifactDetails task={task} jobId={jobId} />
                            }
                            <div className={styles["log-body"]}>
                              {
                                task.output.length === 0 ?
                                  <div className="text-center text-muted">No logs available</div>
                                  :
                                  parseLogLines(task.output)
                              }
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                }
              </div>
            ) :
              <div className="card">
                <div className="card-body">
                  <h5 className="card-title">No tasks available</h5>
                  <p className="card-text">If the job is queued, it has to wait for the previous jobs to finish.</p>
                </div>
              </div>
          }
        </div>
      </div >
    </div >
  );
};

export default JobProcessPage;