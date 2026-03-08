import KareokeRoomModel from "@/models/KareokeRoomModel";

type MetadataUpdate = {
  version: number;
  target: "metadata";
  changes: Record<string, any>;
};

type PlaylistUpdate = {
  version: number;
  target: "playlist";
  item_id: string;
  action: "cleared_to" | "moved_to_top" | "removed"
};

type PlaylistAddedUpdate = {
  version: number;
  target: "playlist";
  action: "added";
  item: PlaylistItem;
};

type SyncUpdate = {
  version: number;
  target: "sync";
  item: KareokeRoomModel;
};

export type UpdateActionType = 'UPDATE_METADATA' | 'REMOVE_SONG' | 'SKIP_TO' | 'PLAY_NEXT';

export type SocketUpdate = MetadataUpdate | PlaylistUpdate | PlaylistAddedUpdate | SyncUpdate;

export type ActionResponse = 
  | {
      status: 'ok';
      request_id: string;
    }
  | {
      status: 'error';
      request_id: string;
      message: string;
    };