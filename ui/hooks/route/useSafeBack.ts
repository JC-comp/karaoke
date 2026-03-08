import { useRouter } from 'next/navigation'; // or 'next/router'

export function useSafeBack() {
    const router = useRouter();

    const safeBack = (fallbackPath = '/') => {
        if (typeof window === 'undefined') return;
        const hasHistory = window.history.length > 1;
        if (hasHistory) {
            router.back();
        } else {
            router.push(fallbackPath);
        }
    };

    return { safeBack };
}