'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCirclePause, faSpinner } from '@fortawesome/free-solid-svg-icons';
import KareokeRoom from '@/components/ktv/KareokeRoom';
import YoutubeEmbbedPlayer from '@/components/players/YoutubeEmbbedPlayer';
import ScheduleYoutubePlayer from '@/components/ktv/players/ScheduleYoutubePlayer';
import KareokeRoomModel from '@/models/ktv';
import { useRoomID } from '@/hooks/ktv';

import styles from './page.module.css'
import './page.css'
import "@/components/tabs/SearchJobTab.css";
import "@/components/ktv/KareokeRoom.css";
import "@/components/ktv/players/ScheduleEmbbedPlayer.css";
import "@/components/players/KTVYoutubePlayer.css";

const Player = ({ kareokeRoomModel, item }: { kareokeRoomModel: KareokeRoomModel; item: PlaylistItem }) => {
  const [shouldPlay, setShouldPlay] = useState(false);
  function onPlayerReady(event: YT.PlayerEvent) {
    if (shouldPlay)
      event.target.playVideo();
  }

  function onPlayerStateChange(event: YT.OnStateChangeEvent) {
    if (event.data == YT.PlayerState.ENDED) {
      kareokeRoomModel?.moveToNextItem();
    }
  }

  function onStateChange(player: YT.Player) {
    if (!kareokeRoomModel) return;
    if (!player || !player.playVideo) return;
    if (shouldPlay) {
      player.playVideo();
    }
    else
      player.pauseVideo();
  };

  useEffect(() => {
    if (!kareokeRoomModel) return;
    if (kareokeRoomModel.is_playing) {
      setShouldPlay(true);
    } else {
      setShouldPlay(false);
    }
  });

  switch (item.type) {
    case 'youtube':
      return <YoutubeEmbbedPlayer
        key={item.item_id} videoId={item.identifier}
        shouldPlay={shouldPlay}
        onStateChange={onStateChange}
        onPlayerReady={onPlayerReady}
        onPlayerStateChange={onPlayerStateChange}
      />;
    case 'schedule':
      return <ScheduleYoutubePlayer
        key={item.item_id} jobId={item.identifier}
        shouldPlay={shouldPlay}
        onStateChange={onStateChange}
        onPlayerReady={onPlayerReady}
        onPlayerStateChange={onPlayerStateChange}
      />;
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
    <div className={`${styles['room-info']} ${isPlaylistOpen ? '' : 'd-none'}`}>
      <KareokeRoom kareokeRoomModel={kareokeRoomModel} setKareokeRoomModel={setKareokeRoomModel} roomID={roomID} setRoomID={setRoomID} version={version} setVersion={setVersion} />
    </div>
  </div>
};