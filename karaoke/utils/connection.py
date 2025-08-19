import json
import queue
import socket
import time
import threading

from ..utils.config import Config, get_logger

PACKET_DELIMITER = '\0'

class Connection:
    def __init__(self, socket: socket.socket, server_side: bool = False):
        self.socket = socket
        self.server_side = server_side
        self.logger = get_logger(__name__, Config().log_level)

        self.read_lock = threading.Lock()
        self.read_queue = queue.Queue() # queue to hold incoming data
        self.read_buffer = bytes() # buffer to hold incomplete data

        self.bye_acked = False
        self.closed = False
        
    def getpeername(self) -> str:
        """
        Get the peer name of the socket.
        """
        try:
            return self.socket.getpeername()[0]
        except Exception as e:
            return 'unknown'

    def log(self, func: callable, message: str, *args, **kwargs) -> None:
        """
        Log a message with the peer name.
        """
        func(f"[{self.getpeername()}] {message}", *args, **kwargs)

    def read(self) -> str:
        """
        Read data from the socket. If the data is not complete, it will
        wait for more data to arrive.
        If more than one packet is received, it will return the first
        complete packet and queue the rest.
        """
        with self.read_lock:
            self.logger.debug(f"There are {self.read_queue.qsize()} packets in the queue")
            if not self.read_queue.empty():
                return self.read_queue.get()
            
            self.logger.debug(f"Start reading from remaining buffer: {self.read_buffer}")
            buffer = bytearray(self.read_buffer)
            while True:
                self.logger.debug("Waiting for data...")
                data = self.socket.recv(1024)
                self.logger.debug(f"Received data: '{data}'")
                if not data:
                    raise RuntimeError('Peer gone')
                buffer.extend(data)
                if PACKET_DELIMITER.encode('utf-8') in buffer:
                    self.logger.debug("Hitting new packet delimiter")
                    packets = bytes(buffer).split(PACKET_DELIMITER.encode('utf-8'))
                    for packet in packets[:-1]:
                        self.logger.debug(f"Received packet: {packet}")
                        data = packet.decode('utf-8')
                        self.read_queue.put(data)
                    self.logger.debug(f"Remaining buffer: {packets[-1]}")
                    self.read_buffer = packets[-1]
                    break
            self.logger.debug(f"There are {self.read_queue.qsize()} packets in the queue")
            return self.read_queue.get()
    
    def json_idle(self) -> dict:
        """
        This method is used to read data from the socket and parse it as JSON.
        It is used when the listener is idle and only waiting for a 'bye' message.
        """
        data = json.loads(self.read())
        if 'error' in data:
            raise RuntimeError(data['error'])
        if 'bye' in data:
            self.bye_acked = True
            self.send(json.dumps({
                'bye': True
            }))
        return data

    def json(self) -> dict:
        """
        Read data from the socket and parse it as JSON. 
        """
        data = self.json_idle()
        if 'bye' in data:
            raise RuntimeError("Peer gone")
        return data
            
    def send(self, message: str) -> None:
        """
        Send a message to the socket. The separator is a null byte.
        """
        message += PACKET_DELIMITER
        self.logger.debug(f"Sending message: {message}")
        self.socket.sendall(message.encode('utf-8'))

    def bye(self) -> None:
        """
        Send a 'bye' message to the socket and wait for the peer to
        acknowledge it.
        """
        if self.bye_acked:
            self.logger.debug("Bye message already acknowledged")
            return
        self.send(json.dumps({
            'bye': True
        }))
        while True:
            try:
                self.json_idle()
            except RuntimeError as e:
                if not self.bye_acked:
                    raise e
            if self.bye_acked:
                self.log(self.logger.debug, "Bye message acknowledged")
                break

    def error(self, message: str) -> None:
        """
        Send an error message to the socket.
        """
        self.send(json.dumps({
            'error': message
        }))

    def close(self) -> None:
        """
        Close the connection. If the connection is server-side, it will
        wait for the peer to acknowledge the bye message before closing.
        """
        if self.closed:
            return
        try:
            self.bye()
        except Exception as e:
            self.log(self.logger.error, f"Error sending bye message: {e}")
        
        # Wait for the peer to acknowledge the bye message
        if self.server_side:
            time.sleep(3)
        self.log(self.logger.info, "Closing connection")
        self.socket.close()
        self.closed = True