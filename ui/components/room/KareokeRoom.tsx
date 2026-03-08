'use client';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowUp, faForward, faPause, faPlay, faTrash, faSpinner, faExternalLink, faListOl, faMicrophone, faMicrophoneSlash } from '@fortawesome/free-solid-svg-icons';
import CopyButton from './CopyButton';
import useRoomNavigation from '@/hooks/route/useRoomParams';
import ChangeRoomModalButton from './ChangeRoomModalButton';
import { useState, useEffect, useRef } from 'react';
import styles from './KareokeRoom.module.css';
import SearchPrompt from './SearchPrompt';
import ResponsiveButton from '../ResponsiveButton';
import KareokeRoomModel from '@/models/KareokeRoomModel';

const PlaylistItemComponent = ({ item }: { item: PlaylistItem | null }) => {
    if (!item) {
        return <>
            <h5 className={styles['track-title']}>Invalid Playlist item</h5>
            <p className={`${styles['artist-name']} text-truncate`}>Item not found.</p>
        </>
    }
    return <>
        <h5 className={styles['track-title']}>{item.title}</h5>
        <p className={`${styles['artist-name']} text-truncate`}>{item.artist}</p>
    </>
}

export default function KareokeRoom({ room }: { room: KareokeRoomModel | null }) {
    const { roomURL, toggleURL } = useRoomNavigation();
    const [fabVisible, setFabVisible] = useState<boolean>(true);
    const roomRef = useRef<HTMLDivElement>(null);

    const [fullRoomURL, setFullRoomURL] = useState('');
    useEffect(() => {
        if (typeof window !== 'undefined' && roomURL) {
            const absolute = new URL(roomURL, window.location.origin).href;
            setFullRoomURL(absolute);
        }
    }, [roomURL]);

    useEffect(() => {
        const closeTimeout = setTimeout(() => {
            setFabVisible(false);
        }, 3000);
        function handle(event: MouseEvent | TouchEvent) {
            const target = event.target as HTMLElement;
            if (roomRef.current?.contains(target))
                return;
            setFabVisible(false);
            clearTimeout(closeTimeout);
        }
        function handleClickOutside(event: MouseEvent) {
            handle(event);
        }
        function handleTouchOutside(event: TouchEvent) {
            handle(event);
        }
        document.addEventListener('click', handleClickOutside);
        document.addEventListener('touchstart', handleTouchOutside);

        return () => {
            document.removeEventListener('click', handleClickOutside);
            document.removeEventListener('touchstart', handleTouchOutside);
        }
    }, []);

    if (!room) {
        return (
            <div className="d-flex justify-content-center align-items-center flex-column p-2 position-sticky top-50">
                <FontAwesomeIcon icon={faSpinner} spin size="2x" />
                <p>Preparing your room...</p>
            </div>
        )
    }

    return <div ref={roomRef} className={styles.container}>
        <div className={`${styles.room} ${fabVisible ? styles.open : ''}`}>
            <div className="text-center">
                <div>
                    <small className="text-muted">Room Name:
                        <button className='btn btn-link ms-2' onClick={toggleURL}>
                            {room.room_name}
                            <FontAwesomeIcon icon={faExternalLink} className="ms-1" />
                        </button>
                    </small>
                </div>

                <div className={`${styles.actions} ${styles.controls}`}>
                    <ChangeRoomModalButton />
                    {
                        fullRoomURL &&
                        <CopyButton
                            textToCopy={fullRoomURL}
                            label={'Share Link'}
                        />
                    }
                </div>
            </div>

            <div className="card">
                <div className="card-header">
                    Now Playing
                </div>
                <div className="card-body">
                    {
                        room.playlist.length > 0 ? <>
                            <PlaylistItemComponent item={room.playlist[0].item} />
                            <div className={styles.controls}>
                                <ResponsiveButton
                                    className={`btn btn-sm ${room.is_playing ? 'btn-secondary' : 'btn-primary'}`}
                                    icon={<FontAwesomeIcon icon={room.is_playing ? faPause : faPlay} />}
                                    onClick={() => room.setPlay(!room.is_playing)}
                                    children={room.is_playing ? 'Pause' : 'Play'}
                                />
                                <ResponsiveButton
                                    className="btn btn-warning btn-sm"
                                    icon={<FontAwesomeIcon icon={faForward} />}
                                    onClick={() => room.deletePlaylistItem(room.playlist[0].id)}
                                    children={'Skip'}
                                />
                                <ResponsiveButton
                                    className={`btn btn-sm ${room.is_vocal_on ? 'btn-info' : 'btn-outline-secondary'}`}
                                    icon={<FontAwesomeIcon icon={room.is_vocal_on ? faMicrophone : faMicrophoneSlash} />}
                                    onClick={() => room.setVocalOn(!room.is_vocal_on)}
                                    children={'Vocal'}
                                />
                            </div>
                        </> : (
                            <p className="text-muted">No song in the queue<SearchPrompt /></p>
                        )
                    }
                </div>
            </div>

            <div className="card">
                <div className="card-header">
                    Coming Up Next
                </div>
                {
                    room.playlist.length > 1
                        ?
                        <ul className={`${styles['playlist-container']} list-group list-group-flush`}>
                            {
                                room.playlist.slice(1).map((record) => (
                                    <li className={`${styles['playlist-item']} list-group-item`} key={record.id}>
                                        <div className="song-info">
                                            <PlaylistItemComponent item={record.item} />
                                        </div>
                                        <div className={styles.controls}>
                                            <ResponsiveButton
                                                className="btn btn-sm btn-danger" icon={<FontAwesomeIcon icon={faTrash} />}
                                                onClick={() => room.deletePlaylistItem(record.id)}
                                                children={null}
                                            />
                                            <ResponsiveButton
                                                className="btn btn-sm btn-info" icon={<FontAwesomeIcon icon={faArrowUp} />}
                                                onClick={() => room.moveItemToTop(record.id)}
                                                children={'First'}
                                            />
                                        </div>
                                    </li>
                                ))
                            }
                        </ul>
                        :
                        <div className="card-body overflow-auto">
                            <p className="text-muted">No upcoming songs<SearchPrompt /></p>
                        </div>
                }

            </div>
        </div>
        <div className={`${styles.fab} btn btn-primary ${fabVisible ? styles.open : ''}`} onClick={() => setFabVisible(!fabVisible)}>
            <FontAwesomeIcon icon={faListOl} size="2x" />
        </div>
    </div>
}