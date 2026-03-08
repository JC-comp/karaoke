import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faExchangeAlt } from '@fortawesome/free-solid-svg-icons';
import ModalButton from '@/components/ModalButton';
import useRoomNavigation from '@/hooks/route/useRoomParams';

export default function ChangeRoomModalButton() {
    const [newRoomID, setNewRoomID] = useState<string>('');
    const { roomID, navigateToRoom } = useRoomNavigation();
    return <ModalButton
        className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-2"
        icon={<FontAwesomeIcon icon={faExchangeAlt} />}
        children={'Change Room'}
        modalProps={{
            size: 'lg',
            centered: true,
        }}
        modelHeader={<span>Change Room</span>}
        modalBody={<div className="mb-3">
            <label htmlFor="roomID" className="form-label">Room ID</label>
            <input
                type="text" className="form-control"
                placeholder={roomID || 'Room name'}
                value={newRoomID} onChange={(e) => setNewRoomID(e.target.value)} />
        </div>}
        onOk={() => {
            if (newRoomID) {
                navigateToRoom(newRoomID);
            }
            setNewRoomID('');
        }}
    />
}
