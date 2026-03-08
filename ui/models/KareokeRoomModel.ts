import { UpdateActionType } from "@/types/updates/room";
import { Socket } from "socket.io-client";

export default class KareokeRoomModel {
    socket: Socket;
    version: number = 0;
    room_name: string = "";
    is_fullscreen: boolean = false;
    is_playing: boolean = false;
    is_vocal_on: boolean = false;
    volume: number = 50;
    playlist: PlaylistRecord[] = [];
    pendingCallback: Record<string, () => void> = {};

    constructor(socket: Socket) {
        this.socket = socket;
    }

    public applyUpdate(version: number, data: Partial<KareokeRoomModel>) {
        Object.assign(this, data);
        this.version = version;
    }

    public onCallback(request_id: string) {
        if (this.pendingCallback[request_id]) {
            this.pendingCallback[request_id]();
            delete this.pendingCallback[request_id];
        }
    }

    operationWrapper(type: UpdateActionType, payload: any) {
        return new Promise<void>((resolve) => {
            const requestId = Math.random().toString(36);
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
            this.socket.emit('action', {
                'request_id': requestId,
                'room_id': this.room_name,
                'type': type,
                'payload': payload
            });
        });
    }

    metadataOperationWrapper(payload: Record<string, any>) {
        return this.operationWrapper('UPDATE_METADATA', payload);
    }

    moveItemToTop(item_id: string) {
        return this.operationWrapper('PLAY_NEXT', {
            'item_id': item_id
        })
    }

    deletePlaylistItem(item_id: string) {
        return this.operationWrapper('REMOVE_SONG', {
            'item_id': item_id
        })
    }

    moveToNextItem() {
        if (this.playlist.length > 0) {
            return this.operationWrapper('REMOVE_SONG', {
                'item_id': this.playlist[0].id
            });
        }
    }

    async setPlay(isPlaying: boolean) {
        if (isPlaying == this.is_playing)
            return;
        return await this.metadataOperationWrapper({
            is_playing: isPlaying,
        });
    }

    async setVocalOn(isVocalOn: boolean) {
        if (isVocalOn == this.is_vocal_on)
            return;
        return await this.metadataOperationWrapper({
            is_vocal_on: isVocalOn,
        });
    }

    async setVolume(volume: number) {
        if (volume == this.volume)
            return;
        return await this.metadataOperationWrapper({
            volume: volume,
        });
    }
}