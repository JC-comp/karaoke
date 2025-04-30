import { useEffect, useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheck } from '@fortawesome/free-solid-svg-icons';

export default function CopyButton({ className, content, icon, text }: { className?: string; content: string; icon: React.ReactNode; text: string }) {
  const [isCopied, setIsCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(content)
      .then(() => {
        setIsCopied(true);
      })
      .catch((err) => {
        console.error('Failed to copy: ', err);
      });
  };

  useEffect(() => {
    if (isCopied) {
      const timer = setTimeout(() => {
        setIsCopied(false);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [isCopied]);

  return (
    <button className={`btn btn-sm ${isCopied ? 'btn-success' : className}`} onClick={handleCopy}>
      {isCopied ? <FontAwesomeIcon icon={faCheck} /> : icon}
      <span>
        {isCopied ? 'Copied' : text}
      </span>
    </button>
  );
}