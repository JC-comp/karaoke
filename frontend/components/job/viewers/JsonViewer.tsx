"use client";
import { useEffect, useState } from "react";
import { useFetchArtifact } from "@/utils/artifact";

export default function JsonViewer({ url, setIsLoading, setError }: { url: string, setIsLoading: (loading: boolean) => void, setError: (error: string) => void }) {
  const data = useFetchArtifact(url, setError, setIsLoading);
  const [ jsonData, setJsonData ] = useState<{[key: string]: string} | null>(null);
  
  useEffect(() => {
    if (!data) return;
    setJsonData(JSON.parse(data));
  }, [data]);

  return (
    jsonData &&
      (
        <table className="table table-bordered table-striped table-hover m-0">
          <tbody>
            {
              Object.entries(jsonData).map(([key, value]) => (
                <tr key={key}>
                  <td className="text-truncate">{key}</td>
                  <td className="text-truncate">
                    {JSON.stringify(value)}
                  </td>
                </tr>
              ))
            }
          </tbody>
        </table>
      )
  );
}