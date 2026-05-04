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
    v = cmd.get_view()
    if v:
        return tuple(round(x, 4) for x in v)
    return v

def set_camera_view(view_matrix):
    """
    Aplica una matriz de vista (cámara) sin alterar el resto de la sesión.
    """
    cmd.set_view(view_matrix, quiet=1)

def get_selections_state():
    """Devuelve un diccionario de selecciones y sus átomos (modelo, index)"""
    seles = cmd.get_names('selections')
    out = {}
    for s in seles:
        if s.startswith("_"): continue
        try:
            out[s] = cmd.index(s)
        except Exception:
            pass
    return out

def apply_selections_state(state_dict):
    """Aplica el estado de selecciones recibidas del Host."""
    for sele_name, atoms in state_dict.items():
        sele_final = f"{sele_name}_host"
        if not atoms:
            cmd.select(sele_final, "none")
            continue
            
        by_obj = {}
        for obj, idx in atoms:
            by_obj.setdefault(obj, []).append(str(idx))
            
        parts = []
        for obj, idxs in by_obj.items():
            parts.append(f"({obj} and index {'+'.join(idxs)})")
            
        sele_str = " or ".join(parts)
        
        cmd.log_close()
        try:
            cmd.select(sele_final, sele_str)
        except Exception:
            pass
        finally:
            if _log_file_path:
                cmd.log_open(_log_file_path)

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

_ignore_next_commands = set()

def get_new_commands():
    """Lee y devuelve los nuevos comandos de PyMOL ejecutados por el usuario local."""
    global _log_file, _ignore_next_commands
    if _log_file is None:
        return []
    
    lines = _log_file.readlines()
    
    # Reconstruir comandos multilinea
    full_commands = []
    current_cmd = ""
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped: continue
        
        if line_stripped.endswith('\\'):
            current_cmd += line_stripped[:-1] + " "
        else:
            current_cmd += line_stripped
            full_commands.append(current_cmd)
            current_cmd = ""
            
    # Solo sincronizar comandos explicitos de representacion/estructura
    allowed_base = [
        "color", "show", "hide", "enable", "disable", "select", 
        "delete", "remove", "alter", "cartoon", "sphere", "surface", 
        "ribbon", "bg_color", "space", "label", "create", 
        "extract", "symexp", "spectrum", "util."
    ]
    allowed_prefixes = tuple(allowed_base + ["cmd." + b for b in allowed_base] + ["set ", "cmd.set("])
    
    cmds = []
    for cmd_str in full_commands:
        cmd_clean = cmd_str.strip()
        
        if cmd_clean in _ignore_next_commands:
            _ignore_next_commands.remove(cmd_clean)
            continue
            
        if any(cmd_clean.startswith(p) for p in allowed_prefixes):
            cmds.append(cmd_clean)
            
    # Evitar crecimiento infinito si hay comandos rotos
    if len(_ignore_next_commands) > 100:
        _ignore_next_commands.clear()
        
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
    """Ejecuta un comando recibido de la red pausando el loop y silenciando el output local."""
    global _ignore_next_commands
    cmd_clean = command_str.strip()
    _ignore_next_commands.add(cmd_clean)
    try:
        if cmd_clean.startswith("cmd.") or cmd_clean.startswith("util."):
            import pymol
            from pymol import util
            exec(cmd_clean, {'cmd': cmd, 'util': util, 'pymol': pymol})
        else:
            cmd.do(command_str)
    except Exception:
        pass
