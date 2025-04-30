"use client";
import { useEffect, useState } from "react";

export function useFetchArtifact(url: string | null, setError: (error: string) => void, setIsLoading?: (loading: boolean) => void) {
    const [data, setData] = useState<string | null>(null);

    useEffect(() => {
        if (!url) return;
        const controller = new AbortController();
        const signal = controller.signal;
        fetch(url, { signal })
            .then((response) => {
                return response.json().catch(() => {
                    throw new Error(response.statusText);
                });
            })
            .then((data) => {
                if (!data.success)
                    throw new Error(data.message);
                setData(data.body);
                if (setIsLoading)
                    setIsLoading(false);
            })
            .catch((error) => {
                if (error.name === 'AbortError')
                    return;
                setError(error.message);
                if (setIsLoading)
                    setIsLoading(false);
            });
        return () => {
            controller.abort();
        }
    }, [url]);

    return data;
}