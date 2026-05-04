import socket
import threading
import json
import struct

class CollabNetwork:
    def __init__(self):
        self.is_host = False
        self.is_connected = False
        self.sock = None
        self.clients = []
        self.callbacks = {}

    def set_callback(self, event_name, func):
        self.callbacks[event_name] = func

    def send_msg(self, sock, msg_type, payload=None, binary_data=None):
        """
        Protocolo:
        [4 bytes: Header Length]
        [Header (JSON str)]
        [4 bytes: Binary Length]
        [Binary Data (optional)]
        """
        header_dict = {"type": msg_type}
        if payload is not None:
            header_dict["payload"] = payload
            
        header = json.dumps(header_dict).encode('utf-8')
        header_len = struct.pack(">I", len(header))
        
        if binary_data:
            bin_len = struct.pack(">I", len(binary_data))
            sock.sendall(header_len + header + bin_len + binary_data)
        else:
            bin_len = struct.pack(">I", 0)
            sock.sendall(header_len + header + bin_len)

    def recv_msg(self, sock):
        def recvall(n):
            data = bytearray()
            while len(data) < n:
                try:
                    packet = sock.recv(n - len(data))
                    if not packet: return None
                    data.extend(packet)
                except:
                    return None
            return data

        header_len_data = recvall(4)
        if not header_len_data: return None, None
        header_len = struct.unpack(">I", header_len_data)[0]

        header_data = recvall(header_len)
        header = json.loads(header_data.decode('utf-8'))

        bin_len_data = recvall(4)
        if not bin_len_data: return header, b''
        bin_len = struct.unpack(">I", bin_len_data)[0]
        
        binary_data = b''
        if bin_len > 0:
            binary_data = recvall(bin_len)

        return header, binary_data

    def start_host(self, port, password):
        self.is_host = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", port))
        self.sock.listen(5)
        self.is_connected = True
        threading.Thread(target=self._accept_clients, args=(password,), daemon=True).start()

    def _accept_clients(self, password):
        while self.is_connected:
            try:
                client_sock, addr = self.sock.accept()
                threading.Thread(target=self._handle_client, args=(client_sock, addr, password), daemon=True).start()
            except:
                break
    
    def _handle_client(self, client_sock, addr, password):
        msg, _ = self.recv_msg(client_sock)
        if msg and msg.get("type") == "handshake" and msg.get("payload", {}).get("password") == password:
            self.send_msg(client_sock, "handshake_ok")
            self.clients.append(client_sock)
            if "on_client_connected" in self.callbacks:
                self.callbacks["on_client_connected"](client_sock, addr)
            
            try:
                while True:
                    data, bin_data = self.recv_msg(client_sock)
                    if not data: break
                    if "on_message" in self.callbacks:
                        self.callbacks["on_message"](data, bin_data, client_sock)
            finally:
                if client_sock in self.clients:
                    self.clients.remove(client_sock)
                try:
                    client_sock.close()
                except:
                    pass
                if "on_client_disconnected" in self.callbacks:
                    self.callbacks["on_client_disconnected"](client_sock)
        else:
            self.send_msg(client_sock, "handshake_fail")
            client_sock.close()

    def connect_to_host(self, host, port, password):
        self.is_host = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, port))
            self.send_msg(self.sock, "handshake", {"password": password})
            resp, _ = self.recv_msg(self.sock)
            if resp and resp.get("type") == "handshake_ok":
                self.is_connected = True
                threading.Thread(target=self._client_loop, daemon=True).start()
                return True
        except:
            pass
            
        if self.sock:
            self.sock.close()
        return False

    def _client_loop(self):
        reason = ""
        try:
            while self.is_connected:
                msg, bin_data = self.recv_msg(self.sock)
                if not msg: 
                    reason = "Servidor cerró la conexión."
                    break
                
                if "on_message" in self.callbacks:
                    self.callbacks["on_message"](msg, bin_data, self.sock)
        except Exception as e:
            reason = str(e)
        finally:
            self.disconnect()
            if "on_disconnected" in self.callbacks:
                self.callbacks["on_disconnected"](reason)

    def broadcast(self, msg_type, payload=None, binary_data=None):
        if self.is_host:
            for c in list(self.clients):
                try:
                    self.send_msg(c, msg_type, payload, binary_data)
                except:
                    self.clients.remove(c)
        else:
            if self.sock:
                self.send_msg(self.sock, msg_type, payload, binary_data)

    def disconnect(self):
        self.is_connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        for c in self.clients:
            try:
                c.close()
            except:
                pass
        self.clients.clear()
