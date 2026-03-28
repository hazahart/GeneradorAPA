import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
import threading
import urllib.request
import webbrowser
import ctypes
import time
import json
import os
from main import obtener_metadatos, generar_apa 

try:
    myappid = 'gvteam.generadorapa.app.1' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class CreadorAPA(tk.Tk):
    def __init__(self):
        super().__init__()
        self.version_actual = "1.1.0"
        self.url_version = "https://raw.githubusercontent.com/hazahart/GeneradorAPA/main/version.txt"
        self.url_descarga = "https://github.com/hazahart/GeneradorAPA/releases/latest"
        self.title(f"Generador de Citas APA - GVTeam (v{self.version_actual})")
        
        try: 
            self.iconbitmap('icono.ico') 
        except Exception: 
            pass 
            
        self.update_idletasks()
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        
        ancho_inicial = min(750, ancho_pantalla - 50)
        alto_inicial = min(780, alto_pantalla - 80)
        
        x = max(0, (ancho_pantalla // 2) - (ancho_inicial // 2))
        y = max(0, (alto_pantalla // 2) - (alto_inicial // 2) - 20)
        
        self.geometry(f"{ancho_inicial}x{alto_inicial}+{x}+{y}")
        self.minsize(620, 520)
        self.configure(padx=20, pady=20)

        self.var_tipo_fuente = tk.StringVar(value="Página Web / Documento Genérico")
        self.var_formato_autor = tk.StringVar(value="Hispano (2 apellidos)")
        self.var_autor = tk.StringVar()
        self.var_corporativo = tk.BooleanVar(value=False)
        self.var_fecha = tk.StringVar()
        self.var_titulo = tk.StringVar()
        self.var_sitio = tk.StringVar()
        self.var_revista = tk.StringVar()
        self.var_volumen = tk.StringVar()
        self.var_numero = tk.StringVar()
        self.var_paginas = tk.StringVar()
        self.var_recuperacion = tk.BooleanVar(value=False)

        self.ultima_ref = []
        self.ultima_cita_p = []
        self.ultima_cita_n = []
        self.coleccion_referencias = []
        self.archivo_datos = "coleccion_apa.json"

        self.crear_widgets()
        self.crear_menu() 
        self.cargar_coleccion()
        self.buscar_actualizaciones(silencioso=True)

    def crear_menu(self):
        barra_menu = tk.Menu(self)
        menu_ayuda = tk.Menu(barra_menu, tearoff=0)
        menu_ayuda.add_command(label="Buscar actualizaciones...", command=lambda: self.buscar_actualizaciones(silencioso=False))
        menu_ayuda.add_separator()
        menu_ayuda.add_command(label="Acerca de...", command=self.mostrar_acerca_de)
        barra_menu.add_cascade(label="Ayuda", menu=menu_ayuda)
        self.config(menu=barra_menu)

    def buscar_actualizaciones(self, silencioso=True):
        def tarea_de_red():
            try:
                url_fresca = f"{self.url_version}?t={int(time.time())}"
                req = urllib.request.Request(url_fresca, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    version_remota = response.read().decode('utf-8').strip()
                v_remota_lista = [int(n) for n in version_remota.split('.') if n.isdigit()]
                v_actual_lista = [int(n) for n in self.version_actual.split('.') if n.isdigit()]
                if v_remota_lista > v_actual_lista:
                    self.after(0, lambda: self.mostrar_dialogo_actualizacion(version_remota))
                elif not silencioso:
                    self.after(0, lambda: messagebox.showinfo("Actualizaciones", f"¡Estás utilizando la última versión!\n\nVersión instalada: v{self.version_actual}\nVersión en el servidor: v{version_remota}"))
            except Exception:
                if not silencioso:
                    self.after(0, lambda: messagebox.showerror("Error de conexión", "No se pudo conectar al servidor."))
        threading.Thread(target=tarea_de_red, daemon=True).start()

    def mostrar_dialogo_actualizacion(self, version_nueva):
        if messagebox.askyesno("¡Actualización Disponible!", f"Versión actual: {self.version_actual}\nNueva versión: {version_nueva}\n\n¿Deseas ir a la página de descarga?"):
            webbrowser.open(self.url_descarga)

    def mostrar_acerca_de(self):
        modal = tk.Toplevel(self)
        modal.title("Acerca de...")
        try: 
            modal.iconbitmap('icono.ico')
        except Exception: 
            pass
        modal.geometry("420x350")
        modal.resizable(False, False)
        modal.transient(self) 
        modal.grab_set()
        ttk.Label(modal, text="Generador de Citas APA", font=("Arial", 14, "bold")).pack(pady=(20, 5))
        ttk.Label(modal, text=f"Versión {self.version_actual}", font=("Arial", 10, "italic")).pack(pady=(0, 15))
        info_frame = ttk.Frame(modal)
        info_frame.pack(pady=5)
        ttk.Label(info_frame, text="Desarrollado por el Equipo GVTeam:", font=("Arial", 10, "bold"), justify="center").pack(pady=(0, 5))
        ttk.Label(info_frame, text="• Gustavo Ramírez Mireles\n• Victoria Maldonado Patiño <3", font=("Arial", 10), justify="center").pack(pady=(0, 10))
        btn_cerrar = ttk.Button(modal, text="Aceptar", command=modal.destroy)
        btn_cerrar.pack(side="bottom", pady=15)

    def crear_widgets(self):
        frame_ext = ttk.LabelFrame(self, text=" 1. Extracción Automática ", padding=10)
        frame_ext.pack(fill="x", pady=(0, 10))
        frame_url = tk.Frame(frame_ext)
        frame_url.pack(fill="x", pady=5)
        frame_url.columnconfigure(1, weight=1)
        ttk.Label(frame_url, text="URL o PDF local:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.entry_url = ttk.Entry(frame_url, font=("Arial", 10))
        self.entry_url.grid(row=0, column=1, sticky="ew", padx=(5, 10))
        ttk.Button(frame_url, text="Seleccionar PDF", command=self.seleccionar_archivo).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(frame_url, text="Extraer cita", command=self.procesar_extraccion).grid(row=0, column=3)

        frame_tipo = tk.Frame(self)
        frame_tipo.pack(fill="x", pady=(0, 10))
        frame_tipo.columnconfigure(1, weight=1)
        frame_tipo.columnconfigure(3, weight=1)
        ttk.Label(frame_tipo, text="Tipo de Fuente:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 10))
        tipos_fuente = ["Página Web / Documento Genérico", "Revista Académica (Journal)", "Noticia / Periódico", "Video / Multimedia", "Libro"]
        combo_tipo = ttk.Combobox(frame_tipo, textvariable=self.var_tipo_fuente, values=tipos_fuente, state="readonly", width=25)
        combo_tipo.grid(row=0, column=1, sticky="ew")
        
        ttk.Label(frame_tipo, text="Formato de Autor:", font=("Arial", 10, "bold")).grid(row=0, column=2, sticky="w", padx=(15, 10))
        combo_formato = ttk.Combobox(frame_tipo, textvariable=self.var_formato_autor, values=["Hispano (2 apellidos)", "Internacional (1 apellido)"], state="readonly", width=22)
        combo_formato.grid(row=0, column=3, sticky="ew")

        frame_datos = ttk.LabelFrame(self, text=" 2. Datos de la Referencia ", padding=10)
        frame_datos.pack(fill="x", pady=(0, 10))
        frame_datos.columnconfigure(1, weight=1)
        frame_datos.columnconfigure(3, weight=1)

        ttk.Label(frame_datos, text="Autor(es):").grid(row=0, column=0, sticky="w", pady=2)
        
        f_aut = tk.Frame(frame_datos)
        f_aut.grid(row=0, column=1, sticky="ew", pady=2, padx=5)
        ttk.Entry(f_aut, textvariable=self.var_autor).pack(side="left", fill="x", expand=True)
        ttk.Checkbutton(f_aut, text="Corporativo", variable=self.var_corporativo).pack(side="right", padx=(5,0))
        
        ttk.Label(frame_datos, text="Año/Fecha:").grid(row=0, column=2, sticky="w", pady=2, padx=(10, 5))
        ttk.Entry(frame_datos, textvariable=self.var_fecha, width=12).grid(row=0, column=3, sticky="ew", pady=2)

        ttk.Label(frame_datos, text="Título:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(frame_datos, textvariable=self.var_titulo).grid(row=1, column=1, columnspan=3, sticky="ew", pady=2, padx=5)

        ttk.Label(frame_datos, text="Sitio/Editorial:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(frame_datos, textvariable=self.var_sitio).grid(row=2, column=1, sticky="ew", pady=2, padx=5)
        
        ttk.Label(frame_datos, text="Revista:").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(frame_datos, textvariable=self.var_revista).grid(row=3, column=1, sticky="ew", pady=2, padx=5)
        
        frame_rev_nums = tk.Frame(frame_datos)
        frame_rev_nums.grid(row=3, column=2, columnspan=2, sticky="w", pady=2, padx=(10, 0))
        ttk.Label(frame_rev_nums, text="Vol:").pack(side="left")
        ttk.Entry(frame_rev_nums, textvariable=self.var_volumen, width=4).pack(side="left", padx=2)
        ttk.Label(frame_rev_nums, text="Núm:").pack(side="left", padx=(5,0))
        ttk.Entry(frame_rev_nums, textvariable=self.var_numero, width=4).pack(side="left", padx=2)
        ttk.Label(frame_rev_nums, text="Págs:").pack(side="left", padx=(5,0))
        ttk.Entry(frame_rev_nums, textvariable=self.var_paginas, width=8).pack(side="left", padx=2)

        chk_recup = ttk.Checkbutton(frame_datos, text="Añadir fecha de recuperación", variable=self.var_recuperacion, command=self.toggle_calendario)
        chk_recup.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self.cal_recuperacion = DateEntry(frame_datos, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy', state="disabled")
        self.cal_recuperacion.grid(row=4, column=2, sticky="ew", pady=(10, 2), padx=(10, 5))
        self.btn_hoy = ttk.Button(frame_datos, text="Hoy", command=self.set_hoy, state="disabled")
        self.btn_hoy.grid(row=4, column=3, sticky="w", pady=(10, 2))

        btn_generar = ttk.Button(self, text="Generar APA", command=self.ejecutar_generacion)
        btn_generar.pack(pady=(5, 5))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, pady=(5, 0))

        self.tab_actual = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_actual, text="Cita Actual")

        self.tab_coleccion = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_coleccion, text="Colección (0)")

        f_citas = tk.Frame(self.tab_actual)
        f_citas.pack(fill="x", pady=10, padx=10)
        f_citas.columnconfigure(0, weight=1)
        f_citas.columnconfigure(1, weight=1)

        f_cp = tk.Frame(f_citas)
        f_cp.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        lbl_cp = tk.Frame(f_cp)
        lbl_cp.pack(fill="x")
        ttk.Label(lbl_cp, text="Cita Parentética:", font=("Arial", 9, "bold")).pack(side="left")
        ttk.Button(lbl_cp, text="📋", width=3, command=lambda: self.copiar_texto(self.text_cp, self.ultima_cita_p)).pack(side="right")
        self.text_cp = tk.Text(f_cp, height=2, font=("Arial", 10), wrap="word", state="disabled")
        self.text_cp.pack(fill="x", pady=(2,0))

        f_cn = tk.Frame(f_citas)
        f_cn.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        lbl_cn = tk.Frame(f_cn)
        lbl_cn.pack(fill="x")
        ttk.Label(lbl_cn, text="Cita Narrativa:", font=("Arial", 9, "bold")).pack(side="left")
        ttk.Button(lbl_cn, text="📋", width=3, command=lambda: self.copiar_texto(self.text_cn, self.ultima_cita_n)).pack(side="right")
        self.text_cn = tk.Text(f_cn, height=2, font=("Arial", 10), wrap="word", state="disabled")
        self.text_cn.pack(fill="x", pady=(2,0))

        f_ref = tk.Frame(self.tab_actual)
        f_ref.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        lbl_ref = tk.Frame(f_ref)
        lbl_ref.pack(fill="x")
        ttk.Label(lbl_ref, text="Referencia Final:", font=("Arial", 9, "bold")).pack(side="left")
        ttk.Button(lbl_ref, text="➕ Añadir a Colección", command=self.anadir_a_coleccion).pack(side="right", padx=(5,0))
        ttk.Button(lbl_ref, text="📋 Copiar Referencia", command=lambda: self.copiar_texto(self.text_ref, self.ultima_ref)).pack(side="right")
        
        self.text_ref = tk.Text(f_ref, height=4, font=("Arial", 11), wrap="word", state="disabled")
        self.text_ref.pack(fill="both", expand=True, pady=(2, 0))

        f_col_botones = tk.Frame(self.tab_coleccion)
        f_col_botones.pack(fill="x", pady=10, padx=10)
        ttk.Button(f_col_botones, text="🗑️ Vaciar Lista", command=self.vaciar_coleccion).pack(side="left")
        ttk.Button(f_col_botones, text="📋 Copiar Lista Completa", command=self.copiar_coleccion).pack(side="right")

        f_col_text = tk.Frame(self.tab_coleccion)
        f_col_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.text_coleccion = tk.Text(f_col_text, font=("Arial", 11), wrap="word", state="disabled")
        self.text_coleccion.pack(fill="both", expand=True)

        for t in [self.text_cp, self.text_cn, self.text_ref, self.text_coleccion]:
            if t == self.text_coleccion:
                t.tag_configure("normal", font=("Arial", 11), lmargin1=0, lmargin2=40)
                t.tag_configure("italic", font=("Arial", 11, "italic"), lmargin1=0, lmargin2=40)
            else:
                t.tag_configure("normal", font=("Arial", 11))
                t.tag_configure("italic", font=("Arial", 11, "italic"))
            t.bind("<Control-c>", lambda e, txt=t: self.copiar_atajo(txt))
            t.bind("<Control-C>", lambda e, txt=t: self.copiar_atajo(txt))

    def cargar_coleccion(self):
        if os.path.exists(self.archivo_datos):
            try:
                with open(self.archivo_datos, 'r', encoding='utf-8') as f:
                    self.coleccion_referencias = json.load(f)
                self.actualizar_coleccion_ui()
            except Exception:
                pass

    def guardar_coleccion(self):
        try:
            with open(self.archivo_datos, 'w', encoding='utf-8') as f:
                json.dump(self.coleccion_referencias, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def copiar_atajo(self, text_widget):
        if text_widget == self.text_cp: self.copiar_texto(self.text_cp, self.ultima_cita_p)
        elif text_widget == self.text_cn: self.copiar_texto(self.text_cn, self.ultima_cita_n)
        elif text_widget == self.text_ref: self.copiar_texto(self.text_ref, self.ultima_ref)
        elif text_widget == self.text_coleccion: self.copiar_coleccion()
        return "break"

    def seleccionar_archivo(self):
        ruta = filedialog.askopenfilename(title="Selecciona un documento PDF", filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")])
        if ruta:
            self.entry_url.delete(0, tk.END)
            self.entry_url.insert(0, ruta)

    def procesar_extraccion(self):
        entrada = self.entry_url.get().strip()
        if not entrada:
            messagebox.showwarning("Advertencia", "Introduce una URL o ruta válida.")
            return
        datos = obtener_metadatos(entrada)
        if datos:
            self.var_autor.set(datos.get('autor') or "")
            self.var_titulo.set(datos.get('titulo') or "")
            self.var_fecha.set(datos.get('fecha') or "s. f.")
            self.var_sitio.set(datos.get('sitio') or "")
            self.var_revista.set(datos.get('revista') or "")
            self.var_volumen.set(datos.get('volumen') or "")
            self.var_numero.set(datos.get('numero') or "")
            self.var_paginas.set(datos.get('paginas') or "")
            if datos.get('tipo_fuente_sugerido'):
                self.var_tipo_fuente.set(datos.get('tipo_fuente_sugerido'))
            self.var_corporativo.set(datos.get('es_corporativo_sugerido', False))
        else:
            messagebox.showerror("Error", "No se pudieron extraer datos.")

    def toggle_calendario(self):
        state = "normal" if self.var_recuperacion.get() else "disabled"
        self.cal_recuperacion.config(state=state)
        self.btn_hoy.config(state=state)

    def set_hoy(self):
        self.cal_recuperacion.set_date(datetime.today())

    def ejecutar_generacion(self):
        datos_gui = {
            'url': self.entry_url.get().strip(),
            'autor': self.var_autor.get().strip(),
            'titulo': self.var_titulo.get().strip(),
            'fecha': self.var_fecha.get().strip(),
            'sitio': self.var_sitio.get().strip(),
            'revista': self.var_revista.get().strip(),
            'volumen': self.var_volumen.get().strip(),
            'numero': self.var_numero.get().strip(),
            'paginas': self.var_paginas.get().strip()
        }
        tipo_fuente = self.var_tipo_fuente.get()
        formato_autor = "hispano" if "Hispano" in self.var_formato_autor.get() else "anglosajon"
        es_corp = self.var_corporativo.get()
        
        fecha_recup_str = ""
        if self.var_recuperacion.get():
            f_obj = self.cal_recuperacion.get_date()
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            fecha_recup_str = f"{f_obj.day} de {meses[f_obj.month - 1]} de {f_obj.year}"

        resultados = generar_apa(datos_gui, tipo_fuente, fecha_recuperacion=fecha_recup_str, formato_autor=formato_autor, es_corporativo=es_corp)
        self.ultima_ref = resultados["referencia"]
        self.ultima_cita_p = resultados["cita_parentetica"]
        self.ultima_cita_n = resultados["cita_narrativa"]

        self.actualizar_texto(self.text_ref, self.ultima_ref)
        self.actualizar_texto(self.text_cp, self.ultima_cita_p)
        self.actualizar_texto(self.text_cn, self.ultima_cita_n)
        
        self.notebook.select(self.tab_actual)

    def actualizar_texto(self, widget, tuplas):
        widget.config(state="normal")
        widget.delete(1.0, tk.END)
        for texto, estilo in tuplas:
            widget.insert(tk.END, texto, estilo)
        widget.config(state="disabled")

    def anadir_a_coleccion(self):
        if not self.ultima_ref:
            return
        
        texto_plano = "".join([t[0] for t in self.ultima_ref]).strip().lower()
        
        ya_existe = any(ref["plano"] == texto_plano for ref in self.coleccion_referencias)
        if ya_existe:
            messagebox.showinfo("Aviso", "Esta referencia ya está en la colección.")
            return

        self.coleccion_referencias.append({
            "plano": texto_plano,
            "formato": self.ultima_ref
        })
        
        self.coleccion_referencias.sort(key=lambda x: x["plano"])
        self.actualizar_coleccion_ui()
        self.guardar_coleccion()

    def actualizar_coleccion_ui(self):
        self.notebook.tab(self.tab_coleccion, text=f"Colección ({len(self.coleccion_referencias)})")
        self.text_coleccion.config(state="normal")
        self.text_coleccion.delete(1.0, tk.END)
        for item in self.coleccion_referencias:
            for texto, estilo in item["formato"]:
                self.text_coleccion.insert(tk.END, texto, estilo)
            self.text_coleccion.insert(tk.END, "\n\n")
        self.text_coleccion.config(state="disabled")

    def vaciar_coleccion(self):
        if not self.coleccion_referencias:
            return
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que deseas vaciar toda la colección de referencias?"):
            self.coleccion_referencias = []
            self.actualizar_coleccion_ui()
            self.guardar_coleccion()

    def copiar_coleccion(self):
        if not self.coleccion_referencias:
            return
        todas_las_tuplas = []
        for item in self.coleccion_referencias:
            todas_las_tuplas.extend(item["formato"])
            todas_las_tuplas.append(("\n\n", "normal"))
        self.copiar_texto(self.text_coleccion, todas_las_tuplas)

    def copiar_texto(self, widget, tuplas):
        if not tuplas: return "break"
        texto_plano = ""
        html_fragment = ""
        for texto, estilo in tuplas:
            texto_plano += texto
            t_html = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            if estilo == "italic": html_fragment += f"<i>{t_html}</i>"
            else: html_fragment += t_html
        try:
            prefix = "Version:0.9\r\nStartHTML:{0:010d}\r\nEndHTML:{1:010d}\r\nStartFragment:{2:010d}\r\nEndFragment:{3:010d}\r\n"
            html_start, html_end = "<html><body>", "</body></html>"
            fragment_bytes = html_fragment.encode('utf-8')
            html_start_bytes = html_start.encode('utf-8')
            html_end_bytes = html_end.encode('utf-8')
            start_html = 105 
            start_fragment = start_html + len(html_start_bytes)
            end_fragment = start_fragment + len(fragment_bytes)
            end_html = end_fragment + len(html_end_bytes)
            header = prefix.format(start_html, end_html, start_fragment, end_fragment)
            html_bytes = header.encode('utf-8') + html_start_bytes + fragment_bytes + html_end_bytes
            user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
            kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
            kernel32.GlobalAlloc.restype = ctypes.c_void_p
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalUnlock.restype = ctypes.c_int
            user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
            user32.SetClipboardData.restype = ctypes.c_void_p
            user32.OpenClipboard.argtypes = [ctypes.c_void_p]
            user32.OpenClipboard.restype = ctypes.c_int
            
            user32.OpenClipboard(None) 
            user32.EmptyClipboard()
            text_bytes = texto_plano.encode('utf-16le') + b'\0\0'
            hCd_text = kernel32.GlobalAlloc(0x0002, len(text_bytes))
            ptr_text = kernel32.GlobalLock(hCd_text)
            ctypes.memmove(ptr_text, text_bytes, len(text_bytes))
            kernel32.GlobalUnlock(hCd_text)
            user32.SetClipboardData(13, hCd_text)
            
            CF_HTML = user32.RegisterClipboardFormatW("HTML Format")
            hCd_html = kernel32.GlobalAlloc(0x0002, len(html_bytes) + 1)
            ptr_html = kernel32.GlobalLock(hCd_html)
            ctypes.memmove(ptr_html, html_bytes, len(html_bytes))
            ctypes.c_char.from_address(ptr_html + len(html_bytes)).value = b'\0'
            kernel32.GlobalUnlock(hCd_html)
            user32.SetClipboardData(CF_HTML, hCd_html)
            user32.CloseClipboard()
        except Exception:
            self.clipboard_clear()
            self.clipboard_append(texto_plano)
            self.update()
        return "break"

if __name__ == "__main__":
    app = CreadorAPA()
    app.mainloop()