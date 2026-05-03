import random
import string
import threading
from pymol.qt import QtWidgets, QtCore
from . import network, core

class CollabGUI(QtWidgets.QWidget):
    # Señales para comunicar los hilos de red con el hilo principal de la GUI (PyQt)
    sig_status_update = QtCore.Signal(str)
    sig_client_connected = QtCore.Signal(object, object)
    sig_message_received = QtCore.Signal(dict, bytes, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyMOL Collab")
        self.setMinimumWidth(300)
        self.net = network.CollabNetwork()
        self.setup_ui()
        
        # Conectar señales a sus manejadores en la GUI
        self.sig_status_update.connect(self.update_status_label)
        self.sig_client_connected.connect(self._on_client_connected_gui)
        self.sig_message_received.connect(self._on_message_gui)

        # Configurar callbacks de la red
        self.net.set_callback("on_client_connected", self._net_client_connected)
        self.net.set_callback("on_message", self._net_message)

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        tabs = QtWidgets.QTabWidget()
        layout.addWidget(tabs)
        
        # --- Pestaña: Host ---
        host_tab = QtWidgets.QWidget()
        host_layout = QtWidgets.QVBoxLayout(host_tab)
        
        self.host_pass_input = QtWidgets.QLineEdit()
        self.host_pass_input.setPlaceholderText("Contraseña (opcional)")
        host_layout.addWidget(self.host_pass_input)
        
        self.btn_start_host = QtWidgets.QPushButton("Iniciar Sesión (Host)")
        self.btn_start_host.clicked.connect(self.start_host)
        host_layout.addWidget(self.btn_start_host)
        
        host_layout.addStretch()
        tabs.addTab(host_tab, "Ser Host")
        
        # --- Pestaña: Viewer ---
        join_tab = QtWidgets.QWidget()
        join_layout = QtWidgets.QVBoxLayout(join_tab)
        
        self.join_ip_input = QtWidgets.QLineEdit()
        self.join_ip_input.setPlaceholderText("IP del Host (ej. 192.168.1.50)")
        join_layout.addWidget(self.join_ip_input)
        
        self.join_pass_input = QtWidgets.QLineEdit()
        self.join_pass_input.setPlaceholderText("Contraseña")
        join_layout.addWidget(self.join_pass_input)
        
        self.btn_join = QtWidgets.QPushButton("Conectar")
        self.btn_join.clicked.connect(self.join_session)
        join_layout.addWidget(self.btn_join)
        
        join_layout.addStretch()
        tabs.addTab(join_tab, "Unirse")
        
        # --- Estado ---
        self.lbl_status = QtWidgets.QLabel("Estado: Desconectado")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

    def start_host(self):
        password = self.host_pass_input.text()
        if not password:
            # Generar contraseña segura al azar si está vacía
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            self.host_pass_input.setText(password)
        
        try:
            self.net.start_host(5000, password)
            self.sig_status_update.emit(f"Host en Puerto 5000\nClave: {password}")
            self.btn_start_host.setEnabled(False)
        except Exception as e:
            self.sig_status_update.emit(f"Error: {str(e)}")

    def join_session(self):
        ip = self.join_ip_input.text()
        password = self.join_pass_input.text()
        
        self.sig_status_update.emit("Conectando...")
        self.btn_join.setEnabled(False)
        
        # Se lanza en un hilo para no bloquear la GUI mientras conecta
        def _connect():
            success = self.net.connect_to_host(ip, 5000, password)
            if success:
                self.sig_status_update.emit("Conectado. Esperando sesión...")
            else:
                self.sig_status_update.emit("Error de conexión. Revisa IP/Clave.")
                QtCore.QMetaObject.invokeMethod(self.btn_join, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, True))
        
        threading.Thread(target=_connect, daemon=True).start()

    @QtCore.Slot(str)
    def update_status_label(self, msg):
        self.lbl_status.setText(msg)

    # --- Callbacks de Red (Corren en hilos de fondo) ---
    def _net_client_connected(self, client_sock, addr):
        self.sig_client_connected.emit(client_sock, addr)

    def _net_message(self, msg, bin_data, sock):
        self.sig_message_received.emit(msg, bin_data, sock)

    # --- Handlers de la GUI (Corren en el hilo principal) ---
    @QtCore.Slot(object, object)
    def _on_client_connected_gui(self, client_sock, addr):
        self.sig_status_update.emit(f"Cliente conectado: {addr[0]}")
        # Obtener la sesión actual de PyMOL (solo Host hace esto)
        session_bytes = core.get_session_bytes()
        # Enviar la sesión al nuevo cliente
        self.net.send_msg(client_sock, "session_state", binary_data=session_bytes)

    @QtCore.Slot(dict, bytes, object)
    def _on_message_gui(self, msg, bin_data, sock):
        msg_type = msg.get("type")
        
        if msg_type == "session_state" and bin_data:
            self.sig_status_update.emit("Recibiendo sesión...")
            core.load_session_bytes(bin_data)
            self.sig_status_update.emit("Sesión sincronizada y cargada.")

_dialog = None
def show_window():
    global _dialog
    if _dialog is None:
        _dialog = CollabGUI()
    _dialog.show()
