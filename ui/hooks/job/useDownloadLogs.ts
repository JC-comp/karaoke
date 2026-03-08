import { TaskInfo } from '@/models/TaskInfo';
import { useState, useEffect, useCallback, useRef } from 'react';

export function useDownloadLogs(task: TaskInfo) {
  const [logs, setLogs] = useState<Record<string, any>[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const tokenRef = useRef<string | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      let url = `/api/job/${task.jid}/${task.tid}/logs`;
      // if (tokenRef.current) {
      //   url += `?token=${tokenRef.current}`;
      // }
      
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`);
      }

      const data = await response.json();
      const newContent = data.body.content || [];
      const newToken = data.body.continuation_token || null;
      if (newContent.length > 0) {
          setLogs(newContent);
        // if (tokenRef.current)
        //   setLogs((prev) => [...prev, ...newContent]);
        // else
        //   setLogs(newContent);
      }
      
      tokenRef.current = newToken;
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred");
    } finally {
      setLoading(false);
    }
  }, [task]);

  useEffect(() => {
    tokenRef.current = null;
    fetchLogs();

    if (task.status === 'running') {
      const interval = setInterval(fetchLogs, 3000);
      return () => clearInterval(interval);
    }
  }, [task.status, fetchLogs]);

  return { logs, loading, error };
}