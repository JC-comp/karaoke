'use client';

import React, { useState } from 'react';
import { useSearchParams } from 'next/navigation'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCirclePause, faSpinner } from '@fortawesome/free-solid-svg-icons';
import KareokeRoom from '@/components/ktv/KareokeRoom';
import YoutubeEmbbedPlayer from '@/components/ktv/players/YoutubeEmbbedPlayer';
import ScheduleEmbbedPlayer from '@/components/ktv/players/ScheduleEmbbedPlayer';
import KareokeRoomModel from '@/models/ktv';
import { useRoomID } from '@/hooks/ktv';

import styles from './page.module.css'
import './page.css'
import "@/components/tabs/SearchJobTab.css";
import "@/components/ktv/KareokeRoom.css";
import "@/components/ktv/players/ScheduleEmbbedPlayer.css";

const Player = ({ kareokeRoomModel, item }: { kareokeRoomModel: KareokeRoomModel; item: PlaylistItem }) => {
  switch (item.type) {
    case 'youtube':
      return <YoutubeEmbbedPlayer key={item.item_id} kareokeRoomModel={kareokeRoomModel} videoId={item.identifier} />;
    case 'schedule':
      return <ScheduleEmbbedPlayer key={item.item_id} kareokeRoomModel={kareokeRoomModel} jobId={item.identifier} />;
    default:
      return <div className="d-flex justify-content-center align-items-center">
        Your version of JTV does not support this video type.
      </div>
  }
}

export default function KTVRoom() {
  const searchParams = useSearchParams()
  const encodedRoomID = searchParams.get('roomID');
  const [isPlaylistOpen, setIsPlaylistOpen] = useState(true);
  const [kareokeRoomModel, setKareokeRoomModel] = useState<KareokeRoomModel | null>(null);
  const { roomID, setRoomID } = useRoomID({ encodedRoomID });
  const [version, setVersion] = useState<number>(0);

  return <div className={styles['ktv-room']}>
    <div className={`${styles['video-container']} ${isPlaylistOpen ? styles['open'] : ''}`}>
      {
        !kareokeRoomModel && <div className="d-flex justify-content-center align-items-center">
          <FontAwesomeIcon icon={faSpinner} spin size="2x" />
        </div>
      }
      {
        kareokeRoomModel?.playlist?.[0] ?
          <Player kareokeRoomModel={kareokeRoomModel} item={kareokeRoomModel.playlist[0]} /> :
          <div className="d-flex justify-content-center align-items-center">
            <FontAwesomeIcon icon={faCirclePause} bounce size="2x" />
          </div>
      }
      <button className={styles["toggle-playlist-icon"]} onClick={() => setIsPlaylistOpen(!isPlaylistOpen)}>
        {isPlaylistOpen ? '✕' : '☰'}
      </button>
    </div>
    <div className={`${styles['room-info']} ${isPlaylistOpen ? '': 'd-none'}`}>
      <KareokeRoom kareokeRoomModel={kareokeRoomModel} setKareokeRoomModel={setKareokeRoomModel} roomID={roomID} setRoomID={setRoomID} version={version} setVersion={setVersion} />
    </div>
  </div>
};