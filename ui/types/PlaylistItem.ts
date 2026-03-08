interface PlaylistRecord {
    id: string;
    item: PlaylistItem;
}

interface PlaylistItem {
    item_id: string;
    type: 'youtube' | 'job';
    title: string;
    artist: string;
    identifier: string;
}