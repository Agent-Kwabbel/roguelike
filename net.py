import json
import queue
import socket
import struct
import threading
import zlib

from settings import NET_PORT, MAX_PLAYERS


def local_ip():
    # connecting a udp socket sends nothing, but tells us which network card is used
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


class Connection:
    """One connection between two computers. Messages are dicts, sent as compressed json."""

    def __init__(self, sock):
        self.sock = sock
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.inbox = queue.Queue()
        self.lock = threading.Lock()
        self.closed = False
        threading.Thread(target=self.receive_loop, daemon=True).start()

    def receive_exactly(self, size):
        data = b""
        while len(data) < size:
            part = self.sock.recv(size - len(data))
            if not part:
                return None
            data += part
        return data

    def receive_loop(self):
        while True:
            try:
                header = self.receive_exactly(4)
                if header is None:
                    break
                size = struct.unpack("!I", header)[0]
                data = self.receive_exactly(size)
                if data is None:
                    break
                self.inbox.put(json.loads(zlib.decompress(data)))
            except (OSError, ValueError, zlib.error):
                break
        self.closed = True
        self.inbox.put({"type": "disconnect"})

    def send(self, message):
        if self.closed:
            return
        data = zlib.compress(json.dumps(message, separators=(",", ":")).encode())
        try:
            with self.lock:
                self.sock.sendall(struct.pack("!I", len(data)) + data)
        except OSError:
            self.close()

    def messages(self):
        result = []
        while not self.inbox.empty():
            result.append(self.inbox.get())
        return result

    def close(self):
        if not self.closed:
            self.closed = True
            self.inbox.put({"type": "disconnect"})
        try:
            self.sock.close()
        except OSError:
            pass


class Server:
    """The host waits for other players in the lobby."""

    def __init__(self, port=NET_PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", port))
        self.sock.listen()
        self.sock.settimeout(0.5)
        self.new_connections = queue.Queue()
        self.accepting = True
        self.count = 0
        threading.Thread(target=self.accept_loop, daemon=True).start()

    def accept_loop(self):
        while True:
            try:
                sock, address = self.sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            if not self.accepting or self.count >= MAX_PLAYERS - 1:
                sock.close()
                continue
            sock.settimeout(None)
            self.count += 1
            self.new_connections.put(Connection(sock))

    def new_players(self):
        result = []
        while not self.new_connections.empty():
            result.append(self.new_connections.get())
        return result

    def stop_accepting(self):
        # the socket stays open until the run is over, closing it early can
        # freeze the connections that are already there (seen on WSL)
        self.accepting = False

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


def connect(ip, port=NET_PORT):
    """Returns (connection, None) or (None, error text)."""
    try:
        sock = socket.create_connection((ip, port), timeout=4)
    except OSError as error:
        return None, str(error)
    sock.settimeout(None)
    return Connection(sock), None
