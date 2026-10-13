import json
import os

def cargar_juegos():
    """Lee el archivo plano de juegos."""
    with open('juegos.json', 'r', encoding='utf-8') as archivo:
        return json.load(archivo)

def guardar_usuario(datos_usuario):
    """Guarda un nuevo usuario en el archivo plano."""
    archivo_usuarios = 'usuarios.json'
    usuarios = []

   
    if os.path.exists(archivo_usuarios):
        with open(archivo_usuarios, 'r', encoding='utf-8') as archivo:
            try:
                usuarios = json.load(archivo)
            except json.JSONDecodeError:
                usuarios = [] 

   
    usuarios.append(datos_usuario)

    
    with open(archivo_usuarios, 'w', encoding='utf-8') as archivo:
        json.dump(usuarios, archivo, indent=4, ensure_ascii=False)