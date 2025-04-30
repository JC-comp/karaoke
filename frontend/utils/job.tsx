import { toast } from 'react-toastify';
import { useRouter } from 'next/navigation';

export const submitJob = (formData: FormData, setIsProcessing?: (isProcessing: boolean) => void) => {
    setIsProcessing?.(true);
    return fetch('/api/create-job', {
        method: 'POST',
        body: formData,
    }).then((response) => {
        return response.json().catch(() => {
            throw new Error(response.statusText);
        });
    }).then((jobData) => {
        if (!jobData.success) {
            throw new Error(jobData.message);
        }
        return jobData.body.jid;
    }).finally(() => {
        setIsProcessing?.(false);
    });
}

export const useSubmitJob = () => {
    const router = useRouter();
    const toastWrapper = (formData: FormData, setIsProcessing: (isProcessing: boolean) => void) => {
        toast.info('Submitting data and retrieving job info...', {
            autoClose: false,
            isLoading: true,
            draggable: false,
        });
        submitJob(formData, setIsProcessing)
            .finally(() => {
                toast.dismiss(); // Dismiss the loading toast
            })
            .then((jobId) => {
                toast.success('Job information retrieved successfully!', {
                    autoClose: 2000,
                });
                router.push(`/job?jobId=${jobId}`);
            }).catch((error: any) => {
                toast.error(`Failed to start job: ${error?.message || error}`);
            });
    }
    return toastWrapper;
}

export function capitalizeFirstLetter(string: string) {
    return string.charAt(0).toUpperCase() + string.slice(1).replace('_', ' ');
}