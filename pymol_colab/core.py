from pymol import cmd
import tempfile
import os

def get_session_bytes():
    """
    Guarda la sesión actual de PyMOL en un archivo temporal
    y devuelve su contenido en bytes.
    """
    with tempfile.NamedTemporaryFile(suffix=".pse", delete=False) as tmp:
        tmp_path = tmp.name
    
    # cmd.save() bloquea el hilo principal brevemente mientras guarda
    cmd.save(tmp_path)
    
    with open(tmp_path, "rb") as f:
        data = f.read()
        
    os.remove(tmp_path)
    return data

def load_session_bytes(data):
    """
    Carga una sesión en PyMOL a partir de una secuencia de bytes.
    """
    with tempfile.NamedTemporaryFile(suffix=".pse", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
        
    cmd.load(tmp_path)
    os.remove(tmp_path)

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
