import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';

interface RersponsiveButtonProps {
    className?: string;
    icon: React.ReactNode;
    children: React.ReactNode;
    onClick: () => Promise<void>;
}

export default function RersponsiveButton({ className, icon, children, onClick }: RersponsiveButtonProps) {
    const [isProcessing, setIsProcessing] = useState(false);
    const handleClick = () => {
        setIsProcessing(true);
        onClick()
            .finally(() => {
                setIsProcessing(false);
            });
    };
    return (
        <button className={className}
            onClick={handleClick}
            disabled={isProcessing}
        >
            {isProcessing ? <FontAwesomeIcon icon={faSpinner} spin /> : icon}
            {children && <span>{children}</span>}
        </button>
    )
}