'use client';

import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';
import useRoomNavigation from "@/hooks/route/useRoomParams";
import KareokeRoom from '@/components/room/KareokeRoom';
import styles from './page.module.css'
import { useKTVRoom } from '@/hooks/room/useKTVRoom';
import Player from '@/components/player/Player';

export default function KTVRoom() {
  const [isPlaylistOpen, setIsPlaylistOpen] = useState(true);
  const {roomModel} = useKTVRoom();

  return <div className={styles['ktv-room']}>
    <div className={`${styles['video-container']} ${isPlaylistOpen ? styles['open'] : ''}`}>
      {
        roomModel ?
        <Player room={roomModel} />
        :
        <div className="d-flex justify-content-center align-items-center">
          <FontAwesomeIcon icon={faSpinner} spin size="2x" />
        </div>
      }
      <button className={styles["toggle-playlist-icon"]} onClick={() => setIsPlaylistOpen(!isPlaylistOpen)}>
        {isPlaylistOpen ? '✕' : '☰'}
      </button>
    </div>
    <div className={`${styles['room-info']}`}>
      <KareokeRoom room={roomModel} />
    </div>
  </div>
};