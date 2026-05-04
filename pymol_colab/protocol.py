import json
import struct

# --- Message Types ---
MSG_HANDSHAKE = "handshake"
MSG_HANDSHAKE_OK = "handshake_ok"
MSG_HANDSHAKE_FAIL = "handshake_fail"
MSG_SESSION_STATE = "session_state"
MSG_CAMERA_VIEW = "camera_view"
MSG_COMMAND = "command"
MSG_SELECTIONS = "selections"

def send_message(sock, msg_type, payload=None, binary_data=None):
    """
    Packs and sends a message over a socket.
    Format:
    [4 bytes] Header Length
    [N bytes] Header (JSON string)
    [4 bytes] Binary Data Length
    [M bytes] Binary Data (Optional)
    """
    header_dict = {"type": msg_type}
    if payload is not None:
        header_dict["payload"] = payload
        
    header = json.dumps(header_dict).encode('utf-8')
    header_len = struct.pack(">I", len(header))
    
    if binary_data is not None:
        bin_len = struct.pack(">I", len(binary_data))
        sock.sendall(header_len + header + bin_len + binary_data)
    else:
        bin_len = struct.pack(">I", 0)
        sock.sendall(header_len + header + bin_len)

def recv_message(sock):
    """
    Blocks to read a full message from the socket.
    Returns (header_dict, binary_data).
    Returns (None, None) if the connection closes.
    """
    def recvall(n):
        data = bytearray()
        while len(data) < n:
            try:
                packet = sock.recv(n - len(data))
                if not packet: return None
                data.extend(packet)
            except Exception:
                return None
        return data

    header_len_data = recvall(4)
    if not header_len_data: return None, None
    header_len = struct.unpack(">I", header_len_data)[0]

    header_data = recvall(header_len)
    if not header_data: return None, None
    header = json.loads(header_data.decode('utf-8'))

    bin_len_data = recvall(4)
    if not bin_len_data: return header, b''
    bin_len = struct.unpack(">I", bin_len_data)[0]
    
    binary_data = b''
    if bin_len > 0:
        binary_data = recvall(bin_len)

    return header, binary_data
