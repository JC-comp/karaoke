import React, { useState, useCallback } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCopy, faCheck } from '@fortawesome/free-solid-svg-icons';

interface CopyButtonProps {
  textToCopy: string;
  label?: string;
}

export default function CopyButton({ textToCopy, label }: CopyButtonProps) {
  const [isCopied, setIsCopied] = useState(false);

  const copyAction = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(textToCopy);
      setIsCopied(true);

      // Reset the icon after 2 seconds
      setTimeout(() => setIsCopied(false), 1500);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  }, [textToCopy]);

  return (
    <button
      onClick={copyAction}
      className={`btn ${isCopied ? 'btn-success' : 'btn-outline-primary'} btn-sm d-flex align-items-center gap-2`}
      aria-label="Copy to clipboard"
    >
      <FontAwesomeIcon icon={isCopied ? faCheck : faCopy} />
      {label && <span>{isCopied ? 'Copied!' : label}</span>}
    </button>
  );
}