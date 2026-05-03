#!/bin/bash

# Script simple para empaquetar el plugin en un archivo .zip para PyMOL

PLUGIN_NAME="pymol_colab"
ZIP_NAME="${PLUGIN_NAME}.zip"

# Remover zip anterior si existe
rm -f "$ZIP_NAME"

# Comprimir la carpeta del plugin
echo "Empaquetando el plugin..."
zip -r "$ZIP_NAME" "$PLUGIN_NAME/"

echo "¡Completado! Ahora puedes instalar '$ZIP_NAME' desde el Plugin Manager de PyMOL."
