"use client";
import { useEffect, useState } from "react";
import { useFetchArtifact } from "@/utils/artifact";

export default function PlainViewer({ url, setIsLoading, setError }: { url: string, setIsLoading: (loading: boolean) => void, setError: (error: string) => void }) {
  const data = useFetchArtifact(url, setError, setIsLoading);
  const [plainData, setPlainData] = useState<string | null>(null);

  useEffect(() => {
    setPlainData(data);
  }, [data]);

  return plainData && <div className="overflow-auto">
    <pre className="m-0 p-2 text-break">{plainData}</pre>
  </div>
}