import { useState } from 'react';
import Modal, {ModalProps} from 'react-bootstrap/Modal';

interface ModalButtonProps {
    className: string;
    icon: React.ReactNode;
    children: React.ReactNode;
    modalProps: ModalProps;
    modelHeader: React.ReactNode;
    modalBody: React.ReactNode;
    onOk: () => void;
}

export default function ModalButton({ className, icon, children, modalProps, modelHeader, modalBody, onOk}: ModalButtonProps) {
    const [modalShow, setModalShow] = useState(false);

    return (<>
        <button className={className}
            onClick={() => setModalShow(true)}
        >
            {icon}
            {children && <span>{children}</span>}
        </button>
        <Modal {...modalProps} show={modalShow} onHide={() => setModalShow(false)}>
            <Modal.Header closeButton>
                {modelHeader}
            </Modal.Header>
            <Modal.Body>
                {modalBody}
            </Modal.Body>
            <Modal.Footer>
                <button className="btn btn-secondary" onClick={() => setModalShow(false)}>
                    Close
                </button>
                <button className="btn btn-primary" onClick={() => {
                    onOk();
                    setModalShow(false);
                }}>
                    Save Changes
                </button>
            </Modal.Footer>
        </Modal>
    </>
    )
}