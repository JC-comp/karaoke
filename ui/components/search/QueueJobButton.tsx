import React, { useState } from 'react';
import QueueButton from './QueueButton';
import { QueueItemType, QueuePayload } from '@/types/QueueItem';

export default function QueueJobButton({ searchResult }: { searchResult: SearchResult }) {
  const [jobID, setJobID] = useState<string | null>(null);
  const preprocessor = async (payload: QueuePayload) => {
    let currentJobId = jobID;
    if (!currentJobId) {
      const formData = new FormData();
      formData.append('youtubeLink', `https://youtube.com${searchResult.url_suffix}`);

      const response = await fetch('/api/job/', { method: 'POST', body: formData });
      const jobData = await response.json();
      if (!response.ok || !jobData.success) {
        throw new Error(jobData.message || 'Failed to create job');
      }
      currentJobId = jobData.body.jid;
      setJobID(currentJobId);
    }

    if (!currentJobId)
      throw new Error("Job not found");

    return {
      ...payload,
      item: {
        ...payload.item,
        id: currentJobId
      }
    };
  }
  return <QueueButton
    payload={{
      item_type: 'job',
      item: searchResult
    }}
    preprocessor={preprocessor}
    text='Convert & Queue'
  />
}