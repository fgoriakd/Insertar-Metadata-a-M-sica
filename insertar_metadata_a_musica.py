import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from mutagen import File
from mutagen.id3 import TPE1, TALB, TDRC, TCOM, TIT2, TRCK, APIC
from mutagen.flac import Picture

ruta_portada = None

def seleccionar_portada():
    global ruta_portada
    ruta_portada = filedialog.askopenfilename(
        title="Selecciona la portada del álbum",
        filetypes=[("Archivos de imagen", "*.jpg *.jpeg *.png"), ("Todos los archivos", "*.*")]
    )
    if ruta_portada:
        lbl_portada.config(text=f"Portada: {os.path.basename(ruta_portada)}")

def aplicar_metadata():
    artista = entry_artista.get()
    album = entry_album.get()
    anio = entry_anio.get()
    compositor = entry_compositor.get()
    
    if not archivos_seleccionados:
        messagebox.showwarning("Advertencia", "No hay archivos seleccionados.")
        return

    # Leer la imagen de portada una sola vez si fue seleccionada
    datos_imagen = None
    tipo_mime = "image/jpeg"
    if ruta_portada and os.path.exists(ruta_portada):
        if ruta_portada.lower().endswith('.png'):
            tipo_mime = "image/png"
        with open(ruta_portada, 'rb') as f:
            datos_imagen = f.read()

    # Copiar una portada física (cover.jpg) a la carpeta del álbum para Android
    if ruta_portada and archivos_seleccionados:
        carpeta_album = os.path.dirname(archivos_seleccionados[0])
        destino_cover = os.path.join(carpeta_album, "cover.jpg")
        if not os.path.exists(destino_cover):
            try:
                shutil.copy(ruta_portada, destino_cover)
            except Exception:
                pass

    patron = re.compile(r'^(\d{1,3})[\s\-_\.]+(.+)$')

    for ruta_completa in archivos_seleccionados:
        archivo = os.path.basename(ruta_completa)
        audio = File(ruta_completa, easy=False)
        if audio is None:
            continue
            
        nombre_base = os.path.splitext(archivo)[0]
        
        match = patron.match(nombre_base)
        if match:
            num_pista = match.group(1)
            titulo_limpio = match.group(2).strip()
        else:
            num_pista = ""
            titulo_limpio = nombre_base

        if archivo.lower().endswith('.mp3'):
            if audio.tags is None:
                audio.add_tags()
            tags = audio.tags
            
            # Usamos encoding=1 (UTF-16) compatible con ID3v2.3 para Windows y Android
            if artista: tags.add(TPE1(encoding=1, text=artista))
            if album: tags.add(TALB(encoding=1, text=album))
            if anio: tags.add(TDRC(encoding=1, text=str(anio)))
            if compositor: tags.add(TCOM(encoding=1, text=compositor))
            if num_pista: tags.add(TRCK(encoding=1, text=num_pista))
            tags.add(TIT2(encoding=1, text=titulo_limpio))
            
            if datos_imagen:
                tags.delall("APIC")
                tags.add(APIC(
                    encoding=1,
                    mime=tipo_mime,
                    type=3,  # Portada frontal
                    desc='', 
                    data=datos_imagen
                ))
            # Guardar estrictamente en versión ID3v2.3
            audio.save(v2_version=3)
            
        elif archivo.lower().endswith('.flac'):
            if artista: audio['artist'] = artista
            if album: audio['album'] = album
            if anio: audio['date'] = str(anio)
            if compositor: audio['composer'] = compositor
            if num_pista: audio['tracknumber'] = num_pista
            audio['title'] = titulo_limpio
            
            if datos_imagen:
                audio.clear_pictures()
                picture = Picture()
                picture.type = 3
                picture.mime = tipo_mime
                picture.desc = ''
                picture.data = datos_imagen
                audio.add_picture(picture)
            audio.save()
            
        print(f"Procesado: {archivo} -> [Pista: {num_pista}] [Título: {titulo_limpio}]")

    messagebox.showinfo("Éxito", "¡Metadatos y portada actualizados correctamente!")
    root.destroy()

def seleccionar_archivos():
    global archivos_seleccionados
    archivos_seleccionados = filedialog.askopenfilenames(
        title="Selecciona los archivos de música",
        filetypes=[("Archivos de audio", "*.mp3 *.flac"), ("Todos los archivos", "*.*")]
    )
    if archivos_seleccionados:
        lbl_archivos.config(text=f"{len(archivos_seleccionados)} archivos seleccionados")

root = tk.Tk()
root.title("Editor de Metadatos Musicales")
root.geometry("400x440")

archivos_seleccionados = []

tk.Button(root, text="1. Seleccionar Archivos", command=seleccionar_archivos, bg="#e1e1e1").pack(pady=5)
lbl_archivos = tk.Label(root, text="Ningún archivo seleccionado", fg="gray")
lbl_archivos.pack(pady=2)

tk.Button(root, text="2. Seleccionar Portada (Imagen)", command=seleccionar_portada, bg="#e1e1e1").pack(pady=5)
lbl_portada = tk.Label(root, text="Ninguna portada seleccionada", fg="gray")
lbl_portada.pack(pady=2)

tk.Label(root, text="Artista:").pack()
entry_artista = tk.Entry(root, width=40)
entry_artista.pack()

tk.Label(root, text="Álbum:").pack()
entry_album = tk.Entry(root, width=40)
entry_album.pack()

tk.Label(root, text="Año:").pack()
entry_anio = tk.Entry(root, width=40)
entry_anio.pack()

tk.Label(root, text="Compositor (opcional):").pack()
entry_compositor = tk.Entry(root, width=40)
entry_compositor.pack()

tk.Button(root, text="3. Aplicar Metadatos y Portada", command=aplicar_metadata, bg="#4CAF50", fg="white").pack(pady=15)

root.mainloop()