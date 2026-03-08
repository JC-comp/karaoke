'use client';

import { useMemo, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'react-toastify';

export default function useJobNavigation() {
  const router = useRouter()
  const searchParams = useSearchParams();

  /**
   * 1. EXTRACT & DECODE
   * Reads ?jobId=... from URL and decodes it for the app.
   */
  const jobId = useMemo(() => {
    const encoded = searchParams.get('jobId');
    if (!encoded) return null;

    try {
      // Use atob to decode the Base64 from the URL back to text
      return atob(encoded);
    } catch (e) {
      console.error("Invalid jobId encoding in URL");
      return null;
    }
  }, [searchParams]);

  useEffect(() => {
    if (!jobId) {
      toast.error('Job ID is missing');
      router.push('/');
    }
  }, [jobId, router]);

  return jobId;
}