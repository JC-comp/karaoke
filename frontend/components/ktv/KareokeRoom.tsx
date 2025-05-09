import { useRef, useEffect, useState } from 'react';
import Link from 'next/link';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowUp, faForward, faPause, faPlay, faTrash, faSpinner, faExternalLink, faCopy, faListOl } from '@fortawesome/free-solid-svg-icons';
import { io } from "socket.io-client";
import RersponsiveButton from '@/components/RersponsiveButton';
import ChangeRoomModalButton from './ChangeRoomModalButton';
import CopyButton from './CopyButton';
import KareokeRoomModel from '@/models/ktv';

const PlaylistItemComponent = ({ item }: { item: PlaylistItem }) => {
    return <>
        <h5 className='track-title'>{item.title}</h5>
        <p className='artist-name text-truncate'>{item.artist}</p>
    </>
}

export default function KareokeRoom({ kareokeRoomModel, setKareokeRoomModel, roomID, setRoomID, version, setVersion }: { kareokeRoomModel: KareokeRoomModel | null; setKareokeRoomModel: React.Dispatch<React.SetStateAction<KareokeRoomModel | null>>; roomID: string | null; setRoomID: (roomID: string | null) => void; version: number; setVersion: React.Dispatch<React.SetStateAction<number>> }) {
    const [fabVisible, setFabVisible] = useState<boolean>(true);
    const roomRef = useRef<HTMLDivElement>(null);
    const fabRef = useRef<HTMLDivElement>(null);    

    const generateRoomControlURL = () => {
        var url = `?roomID=${btoa(roomID || '')}#search`;
        if (window.location.pathname !== '/')
            url = '/' + url;

        return url;
    }
    const generateRoomURL = () => {
        return `/ktv?roomID=${btoa(roomID || '')}`;
    }
    const generateRoomOrControllerURL = () => {
        if (window.location.pathname === '/ktv')
            return generateRoomControlURL();
        else
            return generateRoomURL();
    }

    useEffect(() => {
        const socket = io('/ktv', {
            transports: ['websocket'],
            path: '/ws',
        });
        socket.on('connect', () => {
            socket.emit('join', roomID);
        });

        socket.on('update', (data: { request_id: string; body: Room }) => {
            setKareokeRoomModel((prev) => {
                if (prev) {
                    prev.update(data);
                    return prev;
                }
                return KareokeRoomModel.fromJSON(data.body, socket);
            });
            setVersion((prev) => prev + 1);
            setRoomID(data.body.room_name);
        });

        return () => {
            socket.off('connect');
            socket.off('update');
            socket.disconnect();
            setKareokeRoomModel(null);
        }
    }, [roomID]);

    useEffect(() => {
        const closeTimeout = setTimeout(() => {
            setFabVisible(false);
        }, 3000);
        function handle(event: MouseEvent | TouchEvent) {
            const target = event.target as HTMLElement;
            if (roomRef.current?.contains(target) || fabRef.current?.contains(target))
                return;
            setFabVisible(false);
        }
        function handleClickOutside(event: MouseEvent) {
            document.removeEventListener('touchstart', handleTouchOutside);
            handle(event);
        }
        function handleTouchOutside(event: TouchEvent) {
            document.removeEventListener('click', handleClickOutside);
            handle(event);
            clearTimeout(closeTimeout);
        }
        document.addEventListener('click', handleClickOutside);
        document.addEventListener('touchstart', handleTouchOutside);
        
        return () => {
            document.removeEventListener('click', handleClickOutside);
            document.removeEventListener('touchstart', handleTouchOutside);
        }
    }, []);

    if (!kareokeRoomModel) {
        return (
            <div className="d-flex justify-content-center align-items-center flex-column p-2 position-sticky top-50">
                <FontAwesomeIcon icon={faSpinner} spin size="2x" />
                <p>Preparing your room...</p>
            </div>
        )
    }

    const SearchPrompt = () => {
        return <>
            , please add songs with the <Link href={generateRoomControlURL()}>search tab</Link>
        </>;
    }

    return (<div className='kareoke-room-container'>
        <div ref={roomRef} className={`kareoke-room ${fabVisible ? 'open' : ''}`}>
            <div className="room-header">
                <div className="room-info">
                    <small className="text-muted">Room Name:
                        <Link className='ms-2' href={generateRoomOrControllerURL()} >
                            {kareokeRoomModel.room_name}
                            <FontAwesomeIcon icon={faExternalLink} className="ms-1" />
                        </Link>
                    </small>
                </div>
                <div className="room-actions controls">
                    <ChangeRoomModalButton roomID={roomID} setRoomID={setRoomID} />
                    <CopyButton
                        className="btn-outline-info"
                        content={`${window.location.origin}${generateRoomURL()}`}
                        icon={<FontAwesomeIcon icon={faCopy} />}
                        text={'Share Link'}
                    />
                </div>
            </div>

            <div className="card">
                <div className="card-header">
                    Now Playing
                </div>
                <div className="card-body">
                    {
                        kareokeRoomModel.playlist.length > 0 ? <>
                            <PlaylistItemComponent item={kareokeRoomModel.playlist[0]} />
                            <div className="controls">
                                {
                                    <RersponsiveButton
                                        className={`btn btn-sm ${kareokeRoomModel.is_playing ? 'btn-secondary' : 'btn-primary'}`}
                                        icon={<FontAwesomeIcon icon={kareokeRoomModel.is_playing ? faPause : faPlay} />}
                                        onClick={() => kareokeRoomModel.setPlay(!kareokeRoomModel.is_playing)}
                                        children={kareokeRoomModel.is_playing ? 'Pause' : 'Play'}
                                    />
                                }
                                <RersponsiveButton
                                    className="btn btn-warning btn-sm"
                                    icon={<FontAwesomeIcon icon={faForward} />}
                                    onClick={() => kareokeRoomModel.deletePlaylistItem(kareokeRoomModel.playlist[0])}
                                    children={'Skip'}
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
                    kareokeRoomModel.playlist.length > 1
                        ?
                        <ul className="list-group list-group-flush playlist-container">
                            {
                                kareokeRoomModel.playlist.slice(1).map((item) => (
                                    <li className="list-group-item playlist-item" key={item.item_id}>
                                        <div className="song-info">
                                            <PlaylistItemComponent item={item} />
                                        </div>
                                        <div className="controls">
                                            <RersponsiveButton
                                                className="btn btn-sm btn-danger" icon={<FontAwesomeIcon icon={faTrash} />}
                                                onClick={() => kareokeRoomModel.deletePlaylistItem(item)}
                                                children={null}
                                            />
                                            <RersponsiveButton
                                                className="btn btn-sm btn-info" icon={<FontAwesomeIcon icon={faArrowUp} />}
                                                onClick={() => kareokeRoomModel.moveItemToTop(item)}
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
        <div ref={fabRef} className={`fab btn btn-primary ${fabVisible ? 'open' : ''}`} onClick={() => setFabVisible(!fabVisible)}>
            <FontAwesomeIcon icon={faListOl} size="2x" />
        </div>
    </div>
    )
}