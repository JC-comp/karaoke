import React, { useState } from 'react';
import { useSubmitJob } from '@/utils/job';

export default function YoutubeJobTab({ isProcessing, setIsProcessing }: { isProcessing: boolean; setIsProcessing: (isProcessing: boolean) => void }) {
  const [youtubeLink, setYoutubeLink] = useState<string>('');
  const submitJob = useSubmitJob();

  const handleStart = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (youtubeLink === '')
      return;
    event.preventDefault();

    const formData = new FormData();
    formData.append('youtubeLink', youtubeLink);
    submitJob(formData, setIsProcessing)
  };


  return <>
    <label htmlFor="youtubeLink" className="form-label">
      YouTube Link:
    </label>
    <input
      id="youtubeLink"
      className="form-control"
      type="url"
      value={youtubeLink}
      onChange={(event) => setYoutubeLink(event.target.value)}
      placeholder="Enter YouTube video URL"
      required
    />
    <button
      className="btn btn-primary mt-3"
      type='submit'
      onClick={handleStart}
    >
      {isProcessing ? <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> : 'Debug'}
      {isProcessing ? ' Processing...' : ''}
    </button>
  </>
}