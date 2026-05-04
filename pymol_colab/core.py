from pymol import cmd
import tempfile
import os
import threading

def get_session_bytes():
    """
    Guarda la sesión actual de PyMOL en un archivo temporal
    y devuelve su contenido en bytes.
    """
    with tempfile.NamedTemporaryFile(suffix=".pse", delete=False) as tmp:
        tmp_path = tmp.name
    
    import time
    
    cmd.save(tmp_path)
    cmd.sync()  # Pide a PyMOL que termine las tareas pendientes
    
    # Espera activa hasta que PyMOL escriba el archivo
    for _ in range(20):
        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 100:
            break
        time.sleep(0.1)
    
    try:
        with open(tmp_path, "rb") as f:
            data = f.read()
    except Exception:
        data = b''
        
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
        
    return data

def load_session_bytes(data):
    """
    Carga una sesión en PyMOL a partir de una secuencia de bytes.
    """
    with tempfile.NamedTemporaryFile(suffix=".pse", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
        
    cmd.load(tmp_path, quiet=1)
    cmd.sync()
    # PyMOL lee el archivo de manera asíncrona, así que esperamos unos segundos antes de borrarlo
    threading.Timer(5.0, lambda: os.remove(tmp_path) if os.path.exists(tmp_path) else None).start()

def get_camera_view():
    """
    Obtiene la matriz de vista actual (cámara).
    """
    return cmd.get_view()

def set_camera_view(view_matrix):
    """
    Aplica una matriz de vista (cámara) sin alterar el resto de la sesión.
    """
    cmd.set_view(view_matrix, quiet=1)

_log_file_path = None
_log_file = None

def start_command_logging():
    """Abre un log nativo de PyMOL para capturar colores, representaciones y selecciones."""
    global _log_file_path, _log_file
    if _log_file_path is None:
        fd, _log_file_path = tempfile.mkstemp(suffix=".pml", prefix="pymol_colab_")
        os.close(fd)
        cmd.log_open(_log_file_path)
        _log_file = open(_log_file_path, 'r')
        _log_file.seek(0, 2)

def get_new_commands():
    """Lee y devuelve los nuevos comandos de PyMOL ejecutados por el usuario local."""
    global _log_file
    if _log_file is None:
        return []
    lines = _log_file.readlines()
    
    ignore_prefixes = ("turn ", "move ", "zoom ", "orient ", "view ", "set_view")
    cmds = []
    skipping_multiline = False
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped: continue
        
        if skipping_multiline:
            if not line_stripped.endswith('\\'):
                skipping_multiline = False
            continue
            
        if any(line_stripped.startswith(p) for p in ignore_prefixes):
            if line_stripped.endswith('\\'):
                skipping_multiline = True
            continue
            
        cmds.append(line_stripped)
    return cmds

def stop_command_logging():
    global _log_file_path, _log_file
    cmd.log_close()
    if _log_file:
        _log_file.close()
        _log_file = None
    if _log_file_path and os.path.exists(_log_file_path):
        try:
            os.remove(_log_file_path)
        except Exception:
            pass
        _log_file_path = None

def execute_command(command_str):
    """Ejecuta un comando recibido de la red pausando temporalmente el log para evitar loops infinitos."""
    cmd.log_close()
    try:
        cmd.do(command_str)
    except Exception:
        pass
    finally:
        if _log_file_path:
            cmd.log_open(_log_file_path)
