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

interface Word {
    word: string;
    start: number;
    end: number;
}
interface Subtitle {
    start: number;
    end: number;
    alignX: string;
    alignY: string;
    x?: number;
    y?: number;
    bottom?: number;
    font_size: number;
    words: Word[];
}