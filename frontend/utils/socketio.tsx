import { io } from "socket.io-client";

const connectSocketIO = (namespace: string, jobId: string, preJoin: () => void, onError: (error: string) => void) => {
    const socket = io(namespace, {
        transports: ['websocket'],
        path: '/ws',
    });

    var retryTimout: NodeJS.Timeout | null = null;

    const retry = () => {
        if (retryTimout) {
            clearTimeout(retryTimout);
        }
        retryTimout = setTimeout(() => {
            preJoin();
            socket.connect();
        }, 3000);
    }

    const reJoin = () => {
        if (retryTimout) {
            clearTimeout(retryTimout);
        }
        retryTimout = setTimeout(() => {
            preJoin();
            socket.emit('join', jobId);
        }, 3000);
    }

    socket.on('connect', () => {
        console.log('WebSocket connection opened');
        preJoin();
        socket.emit('join', jobId);
    });

    socket.on('disconnect', (reason) => {
        if (reason === 'io server disconnect') {
            onError('Server disconnected the socket');
            retry();
        }
    });

    socket.on('error', (error) => {
        onError(error.message);
        socket.emit('leave', jobId);
        reJoin();
    });

    socket.on('connect_error', (error) => {
        console.log('Connection error:', error);
        onError('Connection error: ' + error.message);
        retry();
    });

    const unsubscribe = () => {
        socket.off('connect');
        socket.off('progress');
        socket.off('disconnect');
        socket.off('error');
        socket.off('connect_error');
        if (retryTimout) {
            clearTimeout(retryTimout);
        }

        socket.disconnect();
    }

    return { socket, unsubscribe };
}

export default connectSocketIO;