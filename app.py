import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
from main import obtener_metadatos, generar_cita_apa 

class CreadorAPA(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Generador de Citas APA 7 - GVTeam")
        
        # --- CENTRAR VENTANA PRINCIPAL EN LA PANTALLA ---
        ancho_ventana = 750
        alto_ventana = 780
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        pos_x = int((ancho_pantalla / 2) - (ancho_ventana / 2))
        pos_y = int((alto_pantalla / 2) - (alto_ventana / 2))
        self.geometry(f"{ancho_ventana}x{alto_ventana}+{pos_x}+{pos_y}")
        
        self.configure(padx=20, pady=20)

        # Variables de control
        self.var_tipo_fuente = tk.StringVar(value="Página Web / Documento Genérico")
        self.var_autor = tk.StringVar()
        self.var_fecha = tk.StringVar()
        self.var_titulo = tk.StringVar()
        self.var_sitio = tk.StringVar()
        
        # Variables exclusivas de revistas
        self.var_revista = tk.StringVar()
        self.var_volumen = tk.StringVar()
        self.var_numero = tk.StringVar()
        self.var_paginas = tk.StringVar()
        
        self.var_recuperacion = tk.BooleanVar(value=False)

        self.crear_widgets()
        self.crear_menu() 

    def crear_menu(self):
        """Crea la barra de menú superior"""
        barra_menu = tk.Menu(self)
        menu_ayuda = tk.Menu(barra_menu, tearoff=0)
        menu_ayuda.add_command(label="Acerca de...", command=self.mostrar_acerca_de)
        barra_menu.add_cascade(label="Ayuda", menu=menu_ayuda)
        self.config(menu=barra_menu)

    def mostrar_acerca_de(self):
        """Muestra una ventana modal centrada respecto a la app principal"""
        modal = tk.Toplevel(self)
        modal.title("Acerca de...")
        
        # --- CENTRAR MODAL RESPECTO A LA VENTANA PRINCIPAL ---
        ancho_modal = 420
        alto_modal = 350
        
        # Actualizamos tareas para tener las dimensiones exactas de la ventana principal
        self.update_idletasks() 
        x_principal = self.winfo_x()
        y_principal = self.winfo_y()
        ancho_principal = self.winfo_width()
        alto_principal = self.winfo_height()
        
        pos_x = x_principal + int((ancho_principal / 2) - (ancho_modal / 2))
        pos_y = y_principal + int((alto_principal / 2) - (alto_modal / 2))
        
        modal.geometry(f"{ancho_modal}x{alto_modal}+{pos_x}+{pos_y}")
        modal.resizable(False, False)
        
        # Bloquear la ventana principal
        modal.transient(self) 
        modal.grab_set()

        # --- Contenido del Modal ---
        ttk.Label(modal, text="Generador de Citas APA 7", font=("Arial", 14, "bold")).pack(pady=(20, 5))
        ttk.Label(modal, text="Versión 1.0.0", font=("Arial", 10, "italic")).pack(pady=(0, 15))

        info_frame = ttk.Frame(modal)
        info_frame.pack(pady=5)

        ttk.Label(info_frame, text="Desarrollado por el Equipo GVTeam:", font=("Arial", 10, "bold"), justify="center").pack(pady=(0, 5))
        ttk.Label(info_frame, text="• Gustavo Ramírez Mireles\n• Victoria Maldonado Patiño", font=("Arial", 10), justify="center").pack(pady=(0, 10))

        ttk.Label(info_frame, text="Ingeniería en Sistemas Computacionales", font=("Arial", 10), justify="center").pack(pady=2)
        ttk.Label(info_frame, text="Materia: Tópicos Avanzados de Desarrollo Web", font=("Arial", 10), justify="center").pack(pady=2)
        ttk.Label(info_frame, text="Docente: Oscar Grimaldo Aguayo", font=("Arial", 10), justify="center").pack(pady=2)
        ttk.Label(info_frame, text="Tecnológico Nacional de México / ITC", font=("Arial", 10, "bold"), justify="center").pack(pady=(5, 2))
        
        ttk.Label(info_frame, text="Tecnología: Python / Tkinter\nAño: 2026", font=("Arial", 10), justify="center").pack(pady=(15, 0))

        btn_cerrar = ttk.Button(modal, text="Aceptar", command=modal.destroy)
        btn_cerrar.pack(side="bottom", pady=15)

    def crear_widgets(self):
        # --- SECCIÓN 1: EXTRACCIÓN ---
        frame_ext = ttk.LabelFrame(self, text=" 1. Extracción Automática ", padding=10)
        frame_ext.pack(fill="x", pady=(0, 15))

        frame_url = tk.Frame(frame_ext)
        frame_url.pack(fill="x", pady=5)
        
        ttk.Label(frame_url, text="URL o PDF local:").pack(side="left")
        self.entry_url = ttk.Entry(frame_url, width=50, font=("Arial", 10))
        self.entry_url.pack(side="left", fill="x", expand=True, padx=(10, 10))

        ttk.Button(frame_url, text="📁 Buscar PDF", command=self.seleccionar_archivo).pack(side="left", padx=(0, 5))
        ttk.Button(frame_url, text="🔍 Extraer", command=self.procesar_extraccion).pack(side="left")

        # --- SECCIÓN 2: TIPO DE FUENTE ---
        frame_tipo = tk.Frame(self)
        frame_tipo.pack(fill="x", pady=(0, 10))
        ttk.Label(frame_tipo, text="Selecciona el Tipo de Fuente APA:", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 10))
        
        tipos_fuente = ["Página Web / Documento Genérico", "Revista Académica (Journal)", "Noticia / Periódico", "Video / Multimedia"]
        combo_tipo = ttk.Combobox(frame_tipo, textvariable=self.var_tipo_fuente, values=tipos_fuente, state="readonly", width=35)
        combo_tipo.pack(side="left")

        # --- SECCIÓN 3: CAMPOS EDITABLES ---
        frame_datos = ttk.LabelFrame(self, text=" 2. Datos de la Cita (Corrige o añade si falta algo) ", padding=10)
        frame_datos.pack(fill="x", pady=(0, 15))

        # Fila 0
        ttk.Label(frame_datos, text="Autor(es):").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(frame_datos, textvariable=self.var_autor, width=40).grid(row=0, column=1, sticky="w", pady=2, padx=5)

        ttk.Label(frame_datos, text="Año/Fecha:").grid(row=0, column=2, sticky="w", pady=2, padx=(15, 5))
        ttk.Entry(frame_datos, textvariable=self.var_fecha, width=15).grid(row=0, column=3, sticky="w", pady=2)

        # Fila 1
        ttk.Label(frame_datos, text="Título:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(frame_datos, textvariable=self.var_titulo, width=80).grid(row=1, column=1, columnspan=3, sticky="w", pady=2, padx=5)

        # Fila 2
        ttk.Label(frame_datos, text="Sitio / Editorial:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(frame_datos, textvariable=self.var_sitio, width=40).grid(row=2, column=1, sticky="w", pady=2, padx=5)
        
        # Fila 3 (Campos de Revista)
        ttk.Label(frame_datos, text="Nombre Revista:").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(frame_datos, textvariable=self.var_revista, width=40).grid(row=3, column=1, sticky="w", pady=2, padx=5)
        
        frame_rev_nums = tk.Frame(frame_datos)
        frame_rev_nums.grid(row=3, column=2, columnspan=2, sticky="w", pady=2, padx=(15, 0))
        
        ttk.Label(frame_rev_nums, text="Vol:").pack(side="left")
        ttk.Entry(frame_rev_nums, textvariable=self.var_volumen, width=5).pack(side="left", padx=2)
        ttk.Label(frame_rev_nums, text="Núm:").pack(side="left", padx=(5,0))
        ttk.Entry(frame_rev_nums, textvariable=self.var_numero, width=5).pack(side="left", padx=2)
        ttk.Label(frame_rev_nums, text="Págs:").pack(side="left", padx=(5,0))
        ttk.Entry(frame_rev_nums, textvariable=self.var_paginas, width=10).pack(side="left", padx=2)

        # Fila 4 (Recuperación)
        chk_recup = ttk.Checkbutton(frame_datos, text="Añadir fecha de recuperación", variable=self.var_recuperacion, command=self.toggle_calendario)
        chk_recup.grid(row=4, column=0, columnspan=2, sticky="w", pady=(15, 2))

        self.cal_recuperacion = DateEntry(frame_datos, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy', state="disabled")
        self.cal_recuperacion.grid(row=4, column=2, sticky="w", pady=(15, 2), padx=(15, 5))

        self.btn_hoy = ttk.Button(frame_datos, text="Hoy", command=self.set_hoy, state="disabled")
        self.btn_hoy.grid(row=4, column=3, sticky="w", pady=(15, 2))

        # --- SECCIÓN 4: GENERACIÓN ---
        btn_generar = ttk.Button(self, text="✨ Generar Cita APA ✨", command=self.ejecutar_generacion)
        btn_generar.pack(pady=(10, 15))

        lbl_resultado = ttk.Label(self, text="Cita Final (Copia y pega en tu documento):", font=("Arial", 10, "bold"))
        lbl_resultado.pack(anchor="w")

        self.text_resultado = tk.Text(self, height=6, width=70, font=("Arial", 11), wrap="word", state="disabled")
        self.text_resultado.pack(fill="both", expand=True)

        self.text_resultado.tag_configure("normal", font=("Arial", 11))
        self.text_resultado.tag_configure("italic", font=("Arial", 11, "italic"))

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
            self.var_fecha.set(datos.get('fecha') or "s.f.")
            self.var_sitio.set(datos.get('sitio') or "")
            self.var_revista.set(datos.get('revista') or "")
            self.var_volumen.set(datos.get('volumen') or "")
            self.var_numero.set(datos.get('numero') or "")
            self.var_paginas.set(datos.get('paginas') or "")
            
            if datos.get('tipo_fuente_sugerido'):
                self.var_tipo_fuente.set(datos.get('tipo_fuente_sugerido'))
        else:
            messagebox.showerror("Error", "No se pudieron extraer datos. Por favor, llénalos manualmente.")

    def toggle_calendario(self):
        if self.var_recuperacion.get():
            self.cal_recuperacion.config(state="normal")
            self.btn_hoy.config(state="normal")
        else:
            self.cal_recuperacion.config(state="disabled")
            self.btn_hoy.config(state="disabled")

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
        
        fecha_recup_str = ""
        if self.var_recuperacion.get():
            f_obj = self.cal_recuperacion.get_date()
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            fecha_recup_str = f"{f_obj.day} de {meses[f_obj.month - 1]} de {f_obj.year}"

        cita_tuplas = generar_cita_apa(datos_gui, tipo_fuente, fecha_recuperacion=fecha_recup_str)

        self.text_resultado.config(state="normal")
        self.text_resultado.delete(1.0, tk.END)

        for texto, estilo in cita_tuplas:
            self.text_resultado.insert(tk.END, texto, estilo)

        self.text_resultado.config(state="disabled")

if __name__ == "__main__":
    app = CreadorAPA()
    app.mainloop()