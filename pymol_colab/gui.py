import random
import string
import threading

try:
    from PyQt5 import QtWidgets, QtCore
    Signal = QtCore.pyqtSignal
    Slot = QtCore.pyqtSlot
except ImportError:
    try:
        from PyQt6 import QtWidgets, QtCore
        Signal = QtCore.pyqtSignal
        Slot = QtCore.pyqtSlot
    except ImportError:
        try:
            from PySide2 import QtWidgets, QtCore
            Signal = QtCore.Signal
            Slot = QtCore.Slot
        except ImportError:
            from PySide6 import QtWidgets, QtCore
            Signal = QtCore.Signal
            Slot = QtCore.Slot

from pymol import cmd
from pymol.wizard import Wizard
from . import network, core

class ConnectionDialog(QtWidgets.QDialog):
    def __init__(self, collab_manager, parent=None):
        super().__init__(parent)
        self.manager = collab_manager
        self.setWindowTitle("Conexión - PyMOL Collab")
        
        # Encontrar ventana padre de PyMOL para que el diálogo no quede detrás
        main_win = None
        for widget in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(widget, QtWidgets.QMainWindow):
                main_win = widget
                break
        if main_win:
            self.setParent(main_win, QtCore.Qt.Window)
            
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        tabs = QtWidgets.QTabWidget()
        layout.addWidget(tabs)
        
        # --- Tab: Host ---
        host_tab = QtWidgets.QWidget()
        host_layout = QtWidgets.QVBoxLayout(host_tab)
        
        host_layout.addWidget(QtWidgets.QLabel("Puerto:"))
        self.host_port_input = QtWidgets.QLineEdit()
        self.host_port_input.setText("56697")
        self.host_port_input.returnPressed.connect(self.start_host)
        host_layout.addWidget(self.host_port_input)
        
        host_layout.addWidget(QtWidgets.QLabel("Contraseña de la Sesión:"))
        self.host_pass_input = QtWidgets.QLineEdit()
        self.host_pass_input.setText(''.join(random.choices(string.ascii_letters + string.digits, k=6)))
        self.host_pass_input.returnPressed.connect(self.start_host)
        host_layout.addWidget(self.host_pass_input)
        
        self.btn_start_host = QtWidgets.QPushButton("Crear Sesión (Host)")
        self.btn_start_host.clicked.connect(self.start_host)
        host_layout.addWidget(self.btn_start_host)
        
        tabs.addTab(host_tab, "Crear Sesión")
        
        # --- Tab: Unirse ---
        join_tab = QtWidgets.QWidget()
        join_layout = QtWidgets.QVBoxLayout(join_tab)
        
        join_layout.addWidget(QtWidgets.QLabel("IP del Host:"))
        self.join_ip_input = QtWidgets.QLineEdit()
        self.join_ip_input.setText("localhost")
        self.join_ip_input.returnPressed.connect(self.join_session)
        join_layout.addWidget(self.join_ip_input)
        
        join_layout.addWidget(QtWidgets.QLabel("Puerto:"))
        self.join_port_input = QtWidgets.QLineEdit()
        self.join_port_input.setText("56697")
        self.join_port_input.returnPressed.connect(self.join_session)
        join_layout.addWidget(self.join_port_input)
        
        join_layout.addWidget(QtWidgets.QLabel("Contraseña:"))
        self.join_pass_input = QtWidgets.QLineEdit()
        self.join_pass_input.returnPressed.connect(self.join_session)
        join_layout.addWidget(self.join_pass_input)
        
        self.btn_join = QtWidgets.QPushButton("Unirse")
        self.btn_join.clicked.connect(self.join_session)
        join_layout.addWidget(self.btn_join)
        
        tabs.addTab(join_tab, "Unirse")

    def start_host(self):
        password = self.host_pass_input.text()
        port_str = self.host_port_input.text()
        port = int(port_str) if port_str.isdigit() else 56697
        self.btn_start_host.setEnabled(False)
        self.manager.start_host(port, password)
        self.close()

    def join_session(self):
        ip = self.join_ip_input.text()
        password = self.join_pass_input.text()
        port_str = self.join_port_input.text()
        port = int(port_str) if port_str.isdigit() else 56697
        self.btn_join.setEnabled(False)
        self.manager.join_session(ip, port, password)
        self.close()

class CollabWizard(Wizard):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def get_prompt(self):
        # El texto que aparece arriba en el visor OpenGL
        self.prompt = [ 'PyMOL Collab: ' + self.manager.status_text ]
        return self.prompt

    def get_panel(self):
        # El menú lateral derecho tipo "Measurement"
        panel = [
            [ 1, 'PyMOL Collab', '' ]
        ]
        
        if self.manager.role == "none":
            panel.append([ 2, 'Conectar...', 'cmd.get_wizard().show_dialog()' ])
        else:
            if self.manager.role == "host":
                panel.append([ 2, 'Sincronizar .pse', 'cmd.get_wizard().force_sync()' ])
            elif self.manager.role == "viewer":
                mode_text = "Seguir Camara" if not self.manager.is_following else "Exploracion Libre"
                panel.append([ 2, mode_text, 'cmd.get_wizard().toggle_camera()' ])
                
            panel.append([ 2, 'Desconectar', 'cmd.get_wizard().disconnect()' ])
            
        panel.append([ 2, 'Cerrar Menu', 'cmd.set_wizard()' ])
        return panel

    def show_dialog(self):
        self.manager.show_connection_dialog()

    def disconnect(self):
        self.manager.disconnect_session()

    def force_sync(self):
        self.manager.force_sync()

    def toggle_camera(self):
        self.manager.toggle_camera_mode()

class CollabManager(QtCore.QObject):
    sig_status_update = Signal(str)
    sig_client_connected = Signal(object, object)
    sig_message_received = Signal(dict, object, object)
    sig_disconnected = Signal(str)
    sig_role_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.net = network.CollabNetwork()
        self.last_view = None
        self.is_following = True
        self.role = "none"
        self.status_text = "Desconectado"
        self.last_objects = None
        
        self.camera_timer = QtCore.QTimer(self)
        self.camera_timer.timeout.connect(self.sync_camera_loop)
        
        self.object_timer = QtCore.QTimer(self)
        self.object_timer.timeout.connect(self.sync_objects_loop)
        
        self.sig_status_update.connect(self.update_status_label)
        self.sig_client_connected.connect(self._on_client_connected_gui)
        self.sig_message_received.connect(self._on_message_gui)
        self.sig_disconnected.connect(self._on_disconnected_gui)
        self.sig_role_changed.connect(self.update_collab_buttons)

        self.net.set_callback("on_client_connected", self._net_client_connected)
        self.net.set_callback("on_message", self._net_message)
        self.net.set_callback("on_disconnected", self._net_disconnected)
        self.net.set_callback("on_client_disconnected", self._net_client_disconnected)

    def show_connection_dialog(self):
        self.dlg = ConnectionDialog(self)
        self.dlg.show()

    def _refresh_wizard(self):
        # Actualiza la UI nativa de PyMOL
        cmd.refresh_wizard()

    def start_host(self, port, password):
        try:
            self.net.start_host(port, password)
            self.sig_status_update.emit(f"Host (P: {port} | C: {password})")
            self.sig_role_changed.emit("host")
        except Exception as e:
            self.sig_status_update.emit(f"Error: {str(e)}")

    def join_session(self, ip, port, password):
        self.sig_status_update.emit(f"Conectando...")
        def _connect():
            success = self.net.connect_to_host(ip, port, password)
            if success:
                self.sig_status_update.emit("Esperando sesion...")
                self.sig_role_changed.emit("viewer")
            else:
                self.sig_status_update.emit("Error de conexion.")
        
        threading.Thread(target=_connect, daemon=True).start()

    def disconnect_session(self):
        self.net.disconnect()
        self.sig_status_update.emit("Desconectado.")
        self.sig_role_changed.emit("none")

    @Slot(str)
    def update_status_label(self, msg):
        self.status_text = msg
        self._refresh_wizard()

    @Slot(str)
    def update_collab_buttons(self, role):
        self.role = role
        if role == "host":
            self.camera_timer.start(100)
            self.last_objects = cmd.get_names('public')
            self.object_timer.start(1000) # Auto-sync cada 1s si cambian los objetos
        elif role == "viewer":
            self.is_following = True
            self.camera_timer.stop()
            self.object_timer.stop()
        else:
            self.camera_timer.stop()
            self.object_timer.stop()
        self._refresh_wizard()

    def toggle_camera_mode(self):
        self.is_following = not self.is_following
        self._refresh_wizard()

    def force_sync(self):
        if self.net.is_host:
            self.sig_status_update.emit("Generando sesion...")
            session_bytes = core.get_session_bytes()
            if session_bytes:
                self.net.broadcast("session_state", binary_data=session_bytes)
                self.sig_status_update.emit("Cambios enviados.")
            else:
                self.sig_status_update.emit("Error generando sesion.")

    @Slot()
    def sync_camera_loop(self):
        if self.net.is_host and self.net.is_connected:
            view = core.get_camera_view()
            if view != self.last_view:
                self.last_view = view
                self.net.broadcast("camera_view", payload=list(view))

    @Slot()
    def sync_objects_loop(self):
        if self.net.is_host and self.net.is_connected:
            current_objects = cmd.get_names('public')
            if current_objects != self.last_objects:
                self.last_objects = current_objects
                self.force_sync()

    def _net_client_connected(self, client_sock, addr):
        self.sig_client_connected.emit(client_sock, addr)

    def _net_message(self, msg, bin_data, sock):
        self.sig_message_received.emit(msg, bin_data, sock)

    def _net_disconnected(self, reason=""):
        self.sig_disconnected.emit(reason)

    def _net_client_disconnected(self, sock):
        pass

    @Slot(object, object)
    def _on_client_connected_gui(self, client_sock, addr):
        try:
            self.sig_status_update.emit(f"Cliente conectado")
            session_bytes = core.get_session_bytes()
            if not session_bytes:
                self.sig_status_update.emit("Error generando sesion.")
                return
                
            self.sig_status_update.emit(f"Enviando sesion...")
            self.net.send_msg(client_sock, "session_state", binary_data=session_bytes)
            self.sig_status_update.emit("Sesion enviada.")
        except Exception as e:
            self.sig_status_update.emit(f"Error Host: {str(e)}")

    @Slot(dict, object, object)
    def _on_message_gui(self, msg, bin_data, sock):
        try:
            msg_type = msg.get("type")
            
            if msg_type == "session_state" and bin_data:
                self.sig_status_update.emit(f"Cargando sesion...")
                core.load_session_bytes(bin_data)
                self.sig_status_update.emit("Sesion sincronizada.")
                
            elif msg_type == "camera_view":
                if not self.net.is_host and self.is_following:
                    view = msg.get("payload")
                    if view:
                        core.set_camera_view(tuple(view))
        except Exception as e:
            self.sig_status_update.emit(f"Error Cliente: {str(e)}")

    @Slot(str)
    def _on_disconnected_gui(self, reason):
        msg = f"Conexion perdida."
        self.sig_status_update.emit(msg)
        self.sig_role_changed.emit("none")


_manager = None
def show_window():
    global _manager
    if _manager is None:
        _manager = CollabManager()
    
    # Activa el menú nativo en la derecha de PyMOL
    cmd.set_wizard(CollabWizard(_manager))
    cmd.refresh_wizard()
    cmd.refresh()
