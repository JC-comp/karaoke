// hooks/useQueueVideo.ts
import { useState, useCallback, useEffect } from 'react';
import { toast } from 'react-toastify';
import useRoomNavigation from '../route/useRoomParams';

export function useQueueVideo() {
    const [isProcessing, setIsProcessing] = useState(false);
    const [isQueued, setIsQueued] = useState(false);
    const { roomID } = useRoomNavigation()

    useEffect(() => {
        setIsQueued(false);
        setIsProcessing(false);
    }, [roomID]);

    const addToQueue = useCallback(async (payload: any) => {
        setIsQueued(false);
        if (!roomID) {
            toast.error('Karaoke room is still loading.');
            return;
        }

        setIsProcessing(true);
        try {
            const res = await fetch('/api/ktv/queue', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...payload, room_id: roomID }),
            });

            const data = await res.json();
            if (!res.ok || !data.success) throw new Error(data.message || 'Error');

            setIsQueued(true);
            return true;
        } catch (err: any) {
            toast.error(`Error: ${err.message}`);
            return false;
        } finally {
            setIsProcessing(false);
        }
    }, [roomID]);

    return { isProcessing, isQueued, addToQueue };
}