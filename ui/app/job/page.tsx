'use client';

import useJobNavigation from '@/hooks/route/useJobParams';
import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimesCircle, faSpinner, faPaperclip, IconDefinition, faExpand, faCompress } from '@fortawesome/free-solid-svg-icons';
import { useJob } from '@/hooks/job/useJob';
import { useSafeBack } from '@/hooks/route/useSafeBack';
import JobPanel from '@/components/job/JobPanel';

export default function JobProcessPage() {
    const jobId = useJobNavigation();
    const { jobs, tasks, error, syncData } = useJob(jobId, true);
    const { safeBack } = useSafeBack();

    const jobInfo = jobId ? jobs[jobId] : null;
    const taskInfos = (jobId ? tasks[jobId] : null) || {};

    if (error) {
        return <div className="root flex-column text-center">
            <FontAwesomeIcon icon={faTimesCircle} className="mb-3 text-danger" size="3x" spin={false} />
            <p className="lead">Failed to load job information</p>
            {jobId && <p className="mt-3">Job ID: {jobId}</p>}
            <div>
                <button className="btn btn-outline-info btn-lg" onClick={() => safeBack()}>
                    Back
                </button>
                <button className="btn btn-info btn-lg m-3" onClick={() => syncData()}>
                    Retry
                </button>
            </div>
        </div>
    }

    if (!jobInfo || !jobId) {
        return <div className="root flex-column text-center">
            <FontAwesomeIcon icon={faSpinner} className="mb-3" size="3x" spin={true} />
            <p className="lead">Loading job information...</p>
            {jobId && <p className="mt-3">Job ID: {jobId}</p>}
            <button className="btn btn-outline-info btn-lg" onClick={() => safeBack()}>
                Back
            </button>
        </div>
    }

    return <div className="container-fluid d-flex flex-column h-100 p-3">
        <div className="d-flex flex-row justify-content-between align-items-center mb-3">
            <button className="btn btn-outline-info btn-lg" onClick={() => safeBack()}>
                Back
            </button>
            <span className="text-start flex-grow-1 px-3">Job: {jobId}</span>
        </div>
        <JobPanel
            jobInfo={jobInfo}
            tasks={taskInfos} />
    </div >
}