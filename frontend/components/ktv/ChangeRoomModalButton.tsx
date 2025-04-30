import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faExchangeAlt } from '@fortawesome/free-solid-svg-icons';
import ModalButton from '@/components/ModalButton';

export default function ChangeRoomModalButton({ roomID, setRoomID }: { roomID: string | null, setRoomID: (roomID: string) => void }) {
    const [newRoomID, setNewRoomID] = useState<string>('');
    return <ModalButton
        className="btn btn-outline-secondary btn-sm"
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
                setRoomID(newRoomID);
            }
            setNewRoomID('');
        }}
    />
}
