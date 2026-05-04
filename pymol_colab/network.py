import socket
import threading
from . import protocol

class CollabNetwork:
    def __init__(self):
        self.is_host = False
        self.is_connected = False
        self.sock = None
        self.clients = []
        self.callbacks = {}

    def set_callback(self, event_name, func):
        self.callbacks[event_name] = func

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
        msg, _ = protocol.recv_message(client_sock)
        if msg and msg.get("type") == protocol.MSG_HANDSHAKE and msg.get("payload", {}).get("password") == password:
            protocol.send_message(client_sock, protocol.MSG_HANDSHAKE_OK)
            self.clients.append(client_sock)
            if "on_client_connected" in self.callbacks:
                self.callbacks["on_client_connected"](client_sock, addr)
            
            try:
                while True:
                    data, bin_data = protocol.recv_message(client_sock)
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
            protocol.send_message(client_sock, protocol.MSG_HANDSHAKE_FAIL)
            client_sock.close()

    def connect_to_host(self, host, port, password):
        self.is_host = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, port))
            protocol.send_message(self.sock, protocol.MSG_HANDSHAKE, {"password": password})
            resp, _ = protocol.recv_message(self.sock)
            if resp and resp.get("type") == protocol.MSG_HANDSHAKE_OK:
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
                msg, bin_data = protocol.recv_message(self.sock)
                if not msg: 
                    reason = "Servidor cerro la conexion."
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
                    protocol.send_message(c, msg_type, payload, binary_data)
                except:
                    self.clients.remove(c)
        else:
            if self.sock:
                protocol.send_message(self.sock, msg_type, payload, binary_data)

    def send_msg(self, client_sock, msg_type, payload=None, binary_data=None):
        # Utilidad para enviar un mensaje a un cliente específico
        protocol.send_message(client_sock, msg_type, payload, binary_data)

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
