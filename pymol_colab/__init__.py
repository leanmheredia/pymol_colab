import sys
import os

def __init_plugin__(app=None):
    """
    Punto de entrada oficial para PyMOL.
    PyMOL ejecuta esta función al cargar el plugin.
    """
    from pymol.plugins import addmenuitemqt
    
    # Esta función se ejecutará al hacer clic en el menú
    def open_gui():
        from . import gui
        gui.show_window()

    # Agrega el botón bajo el menú "Plugin" de PyMOL
    addmenuitemqt('PyMOL Collab', open_gui)
