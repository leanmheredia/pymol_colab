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
    cmd.set_view(view_matrix)
