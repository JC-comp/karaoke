"use client";
import { useEffect, useState } from "react";

export function useFetchArtifact<T = any>(artifact: Artifact) {
    const [data, setData] = useState<T | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);

    useEffect(() => {
        if (!artifact.is_artifact) {
            setIsLoading(false);
            setData(artifact.value);
            return;
        }
        if (artifact.type == 'audio') {
            setIsLoading(false);
            setData(`/artifact/${artifact.value}` as T);
            return;
        }
        setIsLoading(true);
        const url = `/artifact/${artifact.value}`;
        const controller = new AbortController();
        const signal = controller.signal;
        fetch(url, { signal })
            .then((response) => {
                if (!response.ok)
                    throw new Error(`HTTP error! status: ${response.status}`);
                return response.json();
            })
            .then((data) => {
                setData(data);
                setIsLoading(false);
            })
            .catch((error) => {
                if (error.name === 'AbortError') return;
                setError(error.message);
                setIsLoading(false);
            });
        return () => {
            controller.abort();
        }
    }, [artifact]);

    return {
        isLoading, error, data
    };
}