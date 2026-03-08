import { useMemo, useEffect, useState, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { JobInfo } from '@/models/JobInfo';
import { TaskInfo } from '@/models/TaskInfo';

export const useJob = (jobId: string | null, fetchTask: boolean) => {
    const [jobs, setJobs] = useState<{ [key: string]: JobInfo }>({});
    const [rawTasks, setRawTasks] = useState<Record<string, Record<string, TaskInfo>>>({});
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const tasks = useMemo(() => {
        const orderedRecord: Record<string, TaskInfo[]> = {};

        Object.keys(rawTasks).forEach((jid) => {
            const jobTasks = rawTasks[jid];
            const order = jobs[jid]?.task_order;
            if (order) {
                orderedRecord[jid] = order
                    .map(tid => jobTasks[tid])
                    .filter(task => !!task);
            } else {
                orderedRecord[jid] = Object.values(jobTasks);
            }
        });

        return orderedRecord;
    }, [jobs, rawTasks]);

    const socketRef = useRef<Socket | null>(null);

    useEffect(() => {
        if (!jobId) return;
        setIsLoading(true);
        const socket: Socket = io('/job', {
            transports: ['websocket'],
            path: '/ws',
        });
        socketRef.current = socket;

        socket.on('connect', () => {
            socket.emit('join_job', jobId);
            if (fetchTask)
                socket.emit('join_task', jobId);
        });

        socket.on('update_job', (data: Partial<JobInfo>) => {
            const job = new JobInfo();
            job.applyUpdate(data);
            if (job.jid == jobId)
                setIsLoading(false);
            setJobs((prevJobs) => ({ ...prevJobs, [job.jid]: job }));
        });

        socket.on('update_task', (data: Partial<TaskInfo>) => {
            const newTask = new TaskInfo();
            newTask.applyUpdate(data);

            setRawTasks(prevTasks => {
                return {
                    ...prevTasks,
                    [newTask.jid]: {
                        ...(prevTasks[newTask.jid] || {}),
                        [newTask.tid]: newTask
                    }
                }
            });
        });

        socket.on('updated_job', () => {
            setIsLoading(false);
        });
        socket.on('error', (data: { type: string; message?: string; }) => {
            setError(data.message || 'Failed to sync job state');
        });

        // Cleanup on unmount or roomID change
        return () => {
            socket.off('connect');
            socket.off('update_job');
            socket.off('update_task');
            socket.off('updated_job');
            socket.disconnect();
            socketRef.current = null;
            setJobs({});
        };
    }, [jobId]);

    const syncData = useCallback(async () => {
        setIsLoading(true);
        setJobs({});
        setRawTasks({});
        setError(null);

        if (socketRef.current) {
            if (!socketRef.current.connected) {
                socketRef.current.connect();
            }
            // Optional: Emit a join or subscribe event if your backend requires it
            socketRef.current.emit('sync_job', jobId);
            if (fetchTask)
                socketRef.current.emit('sync_task', jobId);
        }
    }, [fetchTask, jobId]);

    return { error, isLoading, jobs, tasks, syncData };
};