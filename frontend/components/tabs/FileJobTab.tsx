import React, { useState, ChangeEvent } from 'react';
import { useSubmitJob } from '@/utils/job';

export default function FileJobTab({ isProcessing, setIsProcessing }: { isProcessing: boolean; setIsProcessing: (isProcessing: boolean) => void }) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const submitJob = useSubmitJob();

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
    } else {
      setSelectedFile(null);
    }
  };

  const handleStart = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (selectedFile === null)
      return;
    event.preventDefault();

    const formData = new FormData();
    formData.append('file', selectedFile);
    submitJob(formData, setIsProcessing)
  };

  return <>
    <label htmlFor="fileUpload" className="form-label">
      Upload File:
    </label>
    <input
      id="fileUpload"
      className="form-control"
      type="file"
      accept=".mp4, .mkv, .avi, .mov, .flv, .wmv"
      onChange={handleFileChange}
      required
    />
    {selectedFile && <p className="text-muted mt-2">Selected file: {selectedFile.name}</p>}
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