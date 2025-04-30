interface PlaylistItem {
    item_id: string;
    type: 'youtube' | 'schedule';
    title: string;
    artist: string;
    identifier: string;
}

interface Room {
    is_fullscreen: boolean;
    is_playing: boolean;
    is_vocal_on: boolean;
    room_name: string;
    version: number;
    volume: number;
    playlist: PlaylistItem[];
}