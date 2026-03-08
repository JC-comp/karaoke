import React, { useState } from 'react';
import { ToastContentProps, toast } from 'react-toastify';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';
import { QueuePayload } from '@/types/QueueItem';
import { useQueueVideo } from '@/hooks/queue/useQueueVideo';

interface QueueButtonProps {
  preprocessor?: (payload: QueuePayload) => Promise<QueuePayload>;
  payload: QueuePayload;
  text: string;
}
const AddConfirmation = ({ closeToast, data }: ToastContentProps<{ add: () => void }>) => {
  return (
    <div className="d-flex flex-column flex-grow-1">
      <div>
        Video already added to queue.
      </div>
      <button className="btn btn-danger btn-sm mt-2 align-self-end"
        onClick={() => {
          closeToast();
          data.add();
        }}
      >
        Add anyway
      </button>
    </div>
  );
};

export default function QueueButton({ payload, preprocessor, text }: QueueButtonProps) {
  const [isPreProcessing, setIsPreProcessing] = useState(false);
  const { isProcessing, isQueued, addToQueue } = useQueueVideo();
  const performRequest = async () => {
    let processedPayload = payload;
    if (preprocessor) {
      try {
        setIsPreProcessing(true);
        processedPayload = await preprocessor(payload);
      } catch (err: any) {
        toast.error(`Error: ${err.message}`);
        return;
      } finally {
        setIsPreProcessing(false);
      }
    }
    addToQueue(processedPayload);
  }
  const handleQueueRequest = () => {
    if (isQueued) {
      toast.warning(AddConfirmation, {
        data: {
          add: () => {
            performRequest();
          }
        }
      });
      return;
    }
    performRequest();
  };

  return (
    <button
      className={`btn ${isQueued ? 'btn-success' : 'btn-secondary'} me-2`}
      onClick={handleQueueRequest}
      disabled={isProcessing || isPreProcessing}
    >
      {(isProcessing || isPreProcessing) ? (
        <FontAwesomeIcon icon={faSpinner} spin />
      ) : isQueued ? (
        'Queued'
      ) : (
        text
      )}
    </button>
  );
}