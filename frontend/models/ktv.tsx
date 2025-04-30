import React from "react";
import { Socket } from "socket.io-client";

export default class KareokeRoomModel {
    is_fullscreen: boolean;
    is_playing: boolean;
    is_vocal_on: boolean;
    room_name: string;
    version: number;
    volume: number;
    playlist: PlaylistItem[];
    socket: Socket | null;
    pendingCallback: Record<string, () => void>;
    constructor(is_fullscreen: boolean, is_playing: boolean, is_vocal_on: boolean, room_name: string, version: number, volume: number, playlist: PlaylistItem[], socket: Socket | null) {
        this.is_fullscreen = is_fullscreen;
        this.is_playing = is_playing;
        this.is_vocal_on = is_vocal_on;
        this.room_name = room_name;
        this.version = version;
        this.volume = volume;
        this.playlist = playlist;
        this.socket = socket;
        this.pendingCallback = {};
    }

    static fromJSON(json: any, socket: Socket): KareokeRoomModel {
        return new KareokeRoomModel(
            json.is_fullscreen,
            json.is_playing,
            json.is_vocal_on,
            json.room_name,
            json.version,
            json.volume,
            json.playlist,
            socket
        );
    }

    update(data: { request_id: string; body: Room }) {
        this.is_fullscreen = data.body.is_fullscreen;
        this.is_playing = data.body.is_playing;
        this.is_vocal_on = data.body.is_vocal_on;
        this.room_name = data.body.room_name;
        this.version = data.body.version;
        this.volume = data.body.volume;
        this.playlist = data.body.playlist;

        if (this.pendingCallback[data.request_id]) {
            this.pendingCallback[data.request_id]();
            delete this.pendingCallback[data.request_id];
        }
    }

    operationWrapper = (opName: string, body: Record<string, any>) => {
        return new Promise<void>((resolve) => {
            const requestId = Math.random().toString(36);
            body['request_id'] = requestId;
            const guard = setTimeout(() => {
                if (this.pendingCallback[requestId]) {
                    delete this.pendingCallback[requestId];
                }
                resolve();
            }, 5000);
            this.pendingCallback[requestId] = () => {
                clearTimeout(guard);
                resolve();
            };
            this.socket?.emit(opName, body);
        });
    }
    playlistItemOperationWrapper = (opName: string, item: PlaylistItem) => {
        return this.operationWrapper(opName, {
            room_id: this.room_name,
            item_id: item.item_id,
        });
    }

    moveItemToTop = (item: PlaylistItem) => {
        return this.playlistItemOperationWrapper('first', item)
    }

    deletePlaylistItem = (item: PlaylistItem) => {
        return this.playlistItemOperationWrapper('delete', item)
    }

    setPlay = (isPlaying: boolean) => {
        return this.operationWrapper('setplay', {
            room_id: this.room_name,
            is_playing: isPlaying,
        });
    }

    moveToNextItem() {
        if (this.playlist.length > 0) {
            this.deletePlaylistItem(this.playlist[0]);
        }
    }
}