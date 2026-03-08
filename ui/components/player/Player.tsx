import React from 'react';
import KareokeRoomModel from "@/models/KareokeRoomModel";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCirclePause } from '@fortawesome/free-solid-svg-icons';
import YoutubeEmbbedPlayer from './YoutubeEmbbedPlayer';
import ScheduleYoutubePlayer from './ScheduleYoutubePlayer';

export default function Player({ room }: { room: KareokeRoomModel }) {
    if (!room.playlist.length) {
        return <div className="d-flex justify-content-center align-items-center">
            <FontAwesomeIcon icon={faCirclePause} bounce size="2x" />
        </div>
    }

    const config = {
        unmanaged: false,
        is_playing: room.is_playing,
        is_vocal_on: room.is_vocal_on,
    };

    function handleStateChange(event: YT.OnStateChangeEvent) {
        if (event.data == YT.PlayerState.ENDED) {
            room.moveToNextItem();
        }
    }

    function handleInfoUpdate(info: Record<string, any>) {
        if (info.muted !== undefined) {
            room.setVocalOn(!info.muted);
        }
    }

    const item = room.playlist[0].item;
    if (!item) {
        return <div className="d-flex justify-content-center align-items-center">
            Invalid Playlist item
        </div>
    }
    switch (item.type) {
        case 'youtube':
            return <YoutubeEmbbedPlayer
                key={item.item_id} videoId={item.identifier}
                config={config}
                handleStateChange={handleStateChange}
                handleInfoUpdate={handleInfoUpdate}
            />;
        case 'job':
            return <ScheduleYoutubePlayer
                key={item.item_id} jobId={item.identifier}
                config={config}
                handleStateChange={handleStateChange}
                handleInfoUpdate={handleInfoUpdate}
            />;
        default:
            return <div className="d-flex justify-content-center align-items-center">
                Your version of JTV does not support this video type.
            </div>
    }
}