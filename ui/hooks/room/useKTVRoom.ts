import KareokeRoomModel from '@/models/KareokeRoomModel';
import { useEffect, useState, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import useRoomNavigation from '../route/useRoomParams';
import { ActionResponse, SocketUpdate } from "@/types/updates/room";


export const useKTVRoom = () => {
    const { roomID, navigateToRoom } = useRoomNavigation();
    const [roomModel, setRoomModel] = useState<KareokeRoomModel | null>(null);

    useEffect(() => {
        const socket: Socket = io('/ktv', {
            transports: ['websocket'],
            path: '/ws',
        });

        socket.on('connect', () => {
            socket.emit('join', roomID);
        });

        socket.on('connect_error', (err) => {
            console.log('WebSocket connect_error', err);
        });

        socket.on('error', (data: { message: string; }) => {
            console.log(data.message);
            setRoomModel(null);
            socket.emit('sync', roomID);
        })

        socket.on('update', (data: SocketUpdate) => {
            if (data.target == 'sync') {
                const model = new KareokeRoomModel(socket);
                model.applyUpdate(data.version, data.item);
                if (model.room_name == roomID) {
                    setRoomModel(model)
                } else {
                    navigateToRoom(model.room_name);
                }
            } else if (data.target == 'metadata') {
                setRoomModel((prev) => {
                    if (!prev) return null;
                    if (data.version !== prev.version + 1) {
                        console.warn(`Version mismatch! Expected ${prev.version + 1}, got ${data.version}. Syncing...`);
                        socket.emit('sync', roomID);
                        return null;
                    }
                    const nextModel = new KareokeRoomModel(socket);
                    Object.assign(nextModel, prev);
                    nextModel.applyUpdate(data.version, data.changes);
                    return nextModel;
                });
            } else if (data.target == 'playlist') {
                setRoomModel((prev) => {
                    if (!prev) return null;
                    if (data.version !== prev.version + 1) {
                        console.warn(`Version mismatch! Expected ${prev.version + 1}, got ${data.version}. Syncing...`);
                        socket.emit('sync', roomID);
                        return null;
                    }
                    const nextModel = new KareokeRoomModel(socket);
                    Object.assign(nextModel, prev);
                    const playlist = [...nextModel.playlist];
                    if (data.action == 'added') {
                        playlist.push({
                            id: data.item.item_id,
                            item: data.item
                        });
                    } else if (data.action == 'cleared_to') {
                        const index = playlist.findIndex(p => p.id === data.item_id);
                        if (index !== -1) {
                            playlist.splice(0, index + 1);
                        }
                    } else if (data.action == 'moved_to_top') {
                        const index = playlist.findIndex(p => p.id === data.item_id);
                        if (index !== -1) {
                            const [item] = playlist.splice(index, 1);
                            playlist.unshift(item);
                        }
                    } else if (data.action == 'removed') {
                        const index = playlist.findIndex(p => p.id === data.item_id);
                        if (index !== -1) {
                            playlist.splice(index, 1);
                        }
                    }
                    nextModel.applyUpdate(data.version, {
                        playlist: playlist
                    });
                    return nextModel;
                });
            }
        });

        socket.on('action_response', (data: ActionResponse) => {
            if (data.status == 'ok') {
                setRoomModel((prev) => {
                    if (prev)
                        prev.onCallback(data.request_id);
                    return prev;
                });
            } else {
                setRoomModel(null);
                socket.emit('sync', roomID);
            }
        });

        // Cleanup on unmount or roomID change
        return () => {
            socket.off('connect');
            socket.off('update');
            socket.disconnect();
            setRoomModel(null);
        };
    }, [roomID]);

    return {
        roomID,
        roomModel
    };
};