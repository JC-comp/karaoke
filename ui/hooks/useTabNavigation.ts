import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function useTabNavigation(setActiveTab?: (tab: string) => void) {
    const router = useRouter();
    const searchParams = useSearchParams();
    if (setActiveTab) {
        useEffect(() => {
            const tab = searchParams.get('tab');
            if (tab) {
                setActiveTab(tab);
            }
        }, [router, searchParams]);
    }

    function navigateToTab(tab: string) {
        const params = new URLSearchParams(searchParams.toString());
        params.set('tab', tab);
        let target = `/?${params.toString()}`;
        if (tab === 'search') {
            target += '#keyword';
        }
        router.push(target);
    }

    return { navigateToTab };
}