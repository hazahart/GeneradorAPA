import os
import fitz
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import json

def es_autor_valido(texto):
    if not texto or not isinstance(texto, str): return False
    t = texto.strip().lower()
    if t.startswith('http://') or t.startswith('https://') or t.startswith('www.'): return False
    if 'wikimedia' in t or 'wikipedia' in t: return False
    basura = ['microsoft', 'word', 'acrobat', 'writer', 'pdf', 'hp', 'usuario']
    for p in basura:
        if p in t: return False
    return True

def es_autor_corporativo(texto):
    if not texto: return False
    pclave = ['universidad', 'organización', 'instituto', 'ministerio', 'departamento', 'nacional', 'centro', 'asociación', 'gobierno', 'corporación', 'fundación', 'agencia', 'comisión', 'consejo', 'sociedad', 'banco', 'fondo', 'programa', 'hospital', 'clínica', 'observatorio', 'secretaría']
    t_lower = texto.lower()
    return any(p in t_lower for p in pclave)

def extraer_metadatos_pdf(doc, origen):
    meta = doc.metadata
    titulo = meta.get("title", "").strip()
    autor = meta.get("author", "").strip()
    fecha = "s. f."
    sitio = ""
    
    match = re.search(r'D:(\d{4})', meta.get("creationDate", ""))
    if match: fecha = match.group(1)

    if len(doc) > 0:
        texto_pag = ""
        for p in range(min(3, len(doc))):
            texto_pag += doc[p].get_text("text") + "\n"
            
        lineas = [linea.strip() for linea in texto_pag.split('\n') if linea.strip()]
        
        if not titulo or titulo.lower() in ["sin título", "untitled", "microsoft word - documento1"]:
            for linea in lineas:
                match_tit = re.search(r'(?i)^(tarea|título|titulo|tema|práctica|practica)\s*:\s*(.*)', linea)
                if match_tit and match_tit.group(2):
                    titulo = match_tit.group(2).strip().capitalize()
                    break
            if not titulo or titulo.lower() in ["sin título", "untitled"]:
                nombre_base = os.path.splitext(os.path.basename(origen))[0]
                nombre_base = re.sub(r'(?i)^dialnet-', '', nombre_base)
                nombre_base = re.sub(r'-\d+$', '', nombre_base)
                nombre_base = re.sub(r'([a-z])([A-Z])', r'\1 \2', nombre_base)
                titulo = nombre_base.replace('-', ' ').replace('_', ' ').strip().capitalize()

        if not autor or not es_autor_valido(autor):
            for i, linea in enumerate(lineas):
                match_aut = re.search(r'(?i)(?:alumno|autor|estudiantes?|nombre|elaboraci[oó]n|elaborado por|elaborada por|escrito por|presentado por|realizado por)\s*[:]?\s*(.+)', linea)
                if match_aut:
                    pos_autor = match_aut.group(1).strip()
                    if pos_autor.lower().endswith(' y') or pos_autor.lower().endswith(' e'):
                        if i + 1 < len(lineas):
                            pos_autor += " " + lineas[i+1].strip()
                    if es_autor_valido(pos_autor):
                        autor = pos_autor.title()
                        break
                
                if '@' in linea and '.' in linea:
                    if any(x in linea.lower() for x in ['editor', 'info@', 'contacto@', 'revista', 'admin', 'redaccion', 'correspondencia', 'editorial', 'ucentral.edu']):
                        continue
                        
                    partes = re.split(r'[|,-]', linea)
                    for p in partes:
                        if '@' not in p and len(p.strip()) > 3:
                            pos_autor = p.strip()
                            if es_autor_valido(pos_autor):
                                autor = pos_autor.title()
                                break
                    
                    if not autor and i > 0:
                        pos_autor = lineas[i-1].strip()
                        if es_autor_valido(pos_autor) and len(pos_autor.split()) >= 2:
                            autor = pos_autor.title()
                    if autor:
                        break

        match_edit = re.search(r'(?i)(?:ediciones|editorial|sello editorial de|publicado por)\s*([A-Za-zÁ-ÉÍÓÚá-éíóúñÑ\s]+)', texto_pag)
        if match_edit:
            sitio_bruto = match_edit.group(1).strip()
            palabras_basura = [' S. A.', ' S.A.', ' S. L. U.', ' S.L.U.', ' LLC', ' Grupo', ' Planeta', ' Penguin', ' Random House']
            for pb in palabras_basura:
                sitio_bruto = re.sub(r'(?i)' + pb, '', sitio_bruto)
            
            sitio_limpio = sitio_bruto.strip().title()
            if len(sitio_limpio) > 2 and len(sitio_limpio) < 30:
                sitio = sitio_limpio

        if fecha == "s. f.":
            match_fecha_ed = re.search(r'(?i)(?:primera edición|impreso en|copyright|©).*?(20\d{2}|19\d{2})', texto_pag)
            if match_fecha_ed:
                fecha = match_fecha_ed.group(1)
            else:
                match_fecha_gen = re.search(r'\b(20\d{2})\b', texto_pag)
                if match_fecha_gen: fecha = match_fecha_gen.group(1)

    tipo_fuente = "Página Web / Documento Genérico"
    if sitio:
        tipo_fuente = "Libro"
    if "dialnet" in origen.lower() or "redalyc" in origen.lower() or "journal" in origen.lower():
        tipo_fuente = "Revista Académica (Journal)"

    return {
        'url': origen, 'autor': autor if es_autor_valido(autor) else None,
        'titulo': titulo if titulo else "Sin título", 'fecha': fecha,
        'sitio': sitio, 'revista': '', 'volumen': '', 'numero': '', 'paginas': '',
        'tipo_fuente_sugerido': tipo_fuente,
        'es_corporativo_sugerido': es_autor_corporativo(autor) if autor else False
    }

def obtener_metadatos(entrada):
    if os.path.isfile(entrada):
        if entrada.lower().endswith('.pdf'):
            try:
                doc = fitz.open(entrada)
                return extraer_metadatos_pdf(doc, entrada)
            except Exception:
                return None
        return None

    try:
        respuesta = requests.get(entrada, impersonate="chrome110", timeout=15)
        if respuesta.status_code != 200: return None
        content_type = respuesta.headers.get('Content-Type', '').lower()
        if 'application/pdf' in content_type or entrada.lower().endswith('.pdf'):
            doc = fitz.open(stream=respuesta.content, filetype="pdf")
            return extraer_metadatos_pdf(doc, entrada)
        html_content = respuesta.content.decode('utf-8')
    except Exception:
        return None

    soup = BeautifulSoup(html_content, 'html.parser')
    metadatos = {
        'url': entrada, 'autor': None, 'titulo': None, 'fecha': "s. f.",
        'sitio': None, 'revista': '', 'volumen': '', 'numero': '', 'paginas': '',
        'tipo_fuente_sugerido': "Página Web / Documento Genérico",
        'es_corporativo_sugerido': False
    }

    og_title = soup.find('meta', property='og:title')
    metadatos['titulo'] = og_title['content'] if og_title and og_title.get('content') else (soup.find('title').text.strip() if soup.find('title') else "Sin título")
    if metadatos['titulo']:
        for sep in [' | ', ' - ', ' – ']:
            if sep in metadatos['titulo']:
                metadatos['titulo'] = metadatos['titulo'].split(sep)[0].strip()
                break

    meta_journal = soup.find('meta', attrs={'name': 'citation_journal_title'})
    if meta_journal: metadatos['revista'] = meta_journal.get('content', '')
    meta_vol = soup.find('meta', attrs={'name': 'citation_volume'})
    if meta_vol: metadatos['volumen'] = meta_vol.get('content', '')
    meta_issue = soup.find('meta', attrs={'name': 'citation_issue'})
    if meta_issue: metadatos['numero'] = meta_issue.get('content', '')
    meta_firstpage = soup.find('meta', attrs={'name': 'citation_firstpage'})
    meta_lastpage = soup.find('meta', attrs={'name': 'citation_lastpage'})
    if meta_firstpage:
        metadatos['paginas'] = meta_firstpage.get('content', '')
        if meta_lastpage: metadatos['paginas'] += f"-{meta_lastpage.get('content', '')}"

    meta_authors = soup.find_all('meta', attrs={'name': 'author'}) + soup.find_all('meta', attrs={'name': 'citation_author'})
    autores_lista = []
    for m_aut in meta_authors:
        cont = m_aut.get('content')
        if cont and es_autor_valido(cont):
            autores_lista.append(cont.strip())
            
    if autores_lista:
        autores_unicos = list(dict.fromkeys(autores_lista))
        metadatos['autor'] = "; ".join(autores_unicos)
    else:
        og_author = soup.find('meta', property='article:author')
        if og_author and es_autor_valido(og_author.get('content')): 
            metadatos['autor'] = og_author['content'].strip()

    meta_pub = soup.find('meta', attrs={'name': 'citation_publisher'}) or \
               soup.find('meta', attrs={'name': 'dc.publisher'}) or \
               soup.find('meta', attrs={'name': 'publisher'}) or \
               soup.find('meta', property='article:publisher')
               
    if meta_pub and meta_pub.get('content') and not meta_pub.get('content').startswith('http'):
        metadatos['sitio'] = meta_pub['content'].strip()
    else:
        og_site = soup.find('meta', property='og:site_name')
        metadatos['sitio'] = og_site['content'] if og_site and og_site.get('content') else urlparse(entrada).netloc.replace('www.', '')

    meta_yt_author = soup.find(attrs={'itemprop': 'author'})
    if meta_yt_author and not metadatos['autor']:
        name_tag = meta_yt_author.find(attrs={'itemprop': 'name'})
        if name_tag and name_tag.get('content'):
            pos_aut = name_tag['content']
        else:
            pos_aut = meta_yt_author.get('content') or meta_yt_author.text
        if pos_aut and es_autor_valido(pos_aut):
            metadatos['autor'] = pos_aut.strip()
            
    meta_yt_date = soup.find(attrs={'itemprop': 'datePublished'}) or soup.find(attrs={'itemprop': 'uploadDate'})
    if meta_yt_date and meta_yt_date.get('content') and metadatos['fecha'] == "s. f.":
        fecha_yt = meta_yt_date['content'][:10]
        partes_f = fecha_yt.split('-')
        if len(partes_f) == 3:
            meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            mes_texto = meses[int(partes_f[1]) - 1]
            metadatos['fecha'] = f"{partes_f[0]}, {int(partes_f[2])} de {mes_texto}"
        else:
            m = re.search(r'\d{4}', meta_yt_date['content'])
            if m: metadatos['fecha'] = m.group(0)

    scripts_json = soup.find_all('script', type='application/ld+json')
    for script in scripts_json:
        try:
            if script.string:
                datos = json.loads(script.string)
                if isinstance(datos, dict): datos = [datos]
                for item in datos:
                    nodos = item.get('@graph', [item])
                    for nodo in nodos:
                        if not metadatos['autor'] and 'author' in nodo:
                            autores_raw = nodo['author']
                            if not isinstance(autores_raw, list): autores_raw = [autores_raw]
                            autores_limpios = []
                            for aut in autores_raw:
                                pos_aut = aut.get('name') if isinstance(aut, dict) else aut
                                if es_autor_valido(pos_aut): autores_limpios.append(pos_aut.strip())
                            if autores_limpios: metadatos['autor'] = "; ".join(autores_limpios)

                        if metadatos['sitio'] == urlparse(entrada).netloc.replace('www.', '') and 'publisher' in nodo:
                            pub = nodo['publisher']
                            if isinstance(pub, dict) and 'name' in pub:
                                metadatos['sitio'] = pub['name']
                            elif isinstance(pub, str):
                                metadatos['sitio'] = pub

                        fecha_str = nodo.get('dateModified') or nodo.get('datePublished')
                        if fecha_str and metadatos['fecha'] == "s. f.":
                            m = re.search(r'\d{4}', fecha_str)
                            if m: metadatos['fecha'] = m.group(0)
        except json.JSONDecodeError: continue

    if metadatos['fecha'] == "s. f.":
        og_pub = soup.find('meta', property='article:published_time') or \
                 soup.find('meta', attrs={'name': 'citation_publication_date'}) or \
                 soup.find('meta', attrs={'name': 'citation_date'}) or \
                 soup.find('meta', property='og:updated_time')
        if og_pub and og_pub.get('content'):
            m = re.search(r'\d{4}', og_pub['content'])
            if m: metadatos['fecha'] = m.group(0)

    url_lower = entrada.lower()
    og_type = soup.find('meta', property='og:type')
    og_type_content = og_type['content'].lower() if og_type and og_type.get('content') else ""

    if metadatos['revista']:
        metadatos['tipo_fuente_sugerido'] = "Revista Académica (Journal)"
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower or 'vimeo.com' in url_lower or 'video' in og_type_content:
        metadatos['tipo_fuente_sugerido'] = "Video / Multimedia"
    elif 'article' in og_type_content or any(domain in url_lower for domain in ['elpais.', 'bbc.', 'cnn.', 'nytimes.', 'france24.', 'elmundo.', 'clarin.', 'noticias']):
        metadatos['tipo_fuente_sugerido'] = "Noticia / Periódico"
        
    if metadatos['autor']:
        metadatos['es_corporativo_sugerido'] = es_autor_corporativo(metadatos['autor'])
        
    return metadatos

def procesar_autores(autor_str, formato="hispano"):
    if not autor_str: return [], []
    
    if ';' in autor_str:
        separadores = r';| y | & '
    elif autor_str.count(',') == 1 and not any(x in autor_str for x in [' y ', ' & ']):
        separadores = r';' 
    else:
        separadores = r',| y | & |;'
        
    autores_brutos = [a.strip() for a in re.split(separadores, autor_str) if a.strip()]
    
    autores_normalizados = []
    for a in autores_brutos:
        if ',' in a:
            partes = [p.strip() for p in a.split(',')]
            if len(partes) == 2:
                autores_normalizados.append(f"{partes[1]} {partes[0]}") 
            else:
                autores_normalizados.append(a.replace(',', ''))
        else:
            autores_normalizados.append(a)
    
    ref_autores = []
    cita_autores = []
    for a in autores_normalizados:
        parts = a.split()
        if len(parts) >= 2 and not a.endswith('.'):
            if formato == "hispano":
                if len(parts) == 2:
                    ref_autores.append(f"{parts[1]}, {parts[0][0]}.")
                    cita_autores.append(parts[1])
                elif len(parts) == 3:
                    ref_autores.append(f"{parts[1]} {parts[2]}, {parts[0][0]}.")
                    cita_autores.append(f"{parts[1]} {parts[2]}")
                else:
                    apellidos = " ".join(parts[-2:])
                    iniciales = " ".join([p[0] + "." for p in parts[:-2]])
                    ref_autores.append(f"{apellidos}, {iniciales}")
                    cita_autores.append(apellidos)
            else:
                apellido = parts[-1]
                iniciales = " ".join([p[0] + "." for p in parts[:-1]])
                ref_autores.append(f"{apellido}, {iniciales}")
                cita_autores.append(apellido)
        else:
            ref_autores.append(a)
            cita_autores.append(a)
            
    return ref_autores, cita_autores

def formatear_autores_ref(autores):
    if not autores: return ""
    if len(autores) == 1: return autores[0]
    if len(autores) == 2: return f"{autores[0]} y {autores[1]}"
    if len(autores) >= 21:
        return ", ".join(autores[:19]) + ", ... " + autores[-1]
    return ", ".join(autores[:-1]) + f" y {autores[-1]}"

def formatear_autores_cita(autores):
    if not autores: return ""
    if len(autores) == 1: return autores[0]
    if len(autores) == 2: return f"{autores[0]} y {autores[1]}"
    return f"{autores[0]} et al."

def generar_apa(datos, tipo_fuente, fecha_recuperacion="", formato_autor="hispano", es_corporativo=False):
    autor_raw = datos.get('autor')
    sitio = datos.get('sitio')
    titulo = datos.get('titulo', 'Sin título')
    fecha = datos.get('fecha', 's. f.')
    url = datos.get('url', '') if str(datos.get('url', '')).startswith('http') else ""
    revista = datos.get('revista', '')
    volumen = datos.get('volumen', '')
    numero = datos.get('numero', '')
    paginas = datos.get('paginas', '')
    editorial = datos.get('sitio', '') 

    ref = []
    cita_p = []
    cita_n = []

    if url and 'wikipedia.org' in url.lower():
        ref.append((f"{titulo}. ", "italic"))
        ref.append((f"({fecha}). En Wikipedia. ", "normal"))
        if url: ref.append((url, "normal"))
        cita_p.append((f"({titulo}, {fecha})", "normal"))
        cita_n.append((f"{titulo} ({fecha})", "normal"))
        return {"referencia": ref, "cita_parentetica": cita_p, "cita_narrativa": cita_n}

    if not autor_raw and sitio:
        autor_raw = sitio
        sitio = ""
        es_corporativo = True

    if es_corporativo:
        if autor_raw:
            autores_corp = [a.strip() for a in re.split(r';| y | & ', autor_raw) if a.strip()]
            if len(autores_corp) > 1:
                if len(autores_corp) == 2:
                    autor_ref = f"{autores_corp[0]} y {autores_corp[1]}"
                else:
                    autor_ref = ", ".join(autores_corp[:-1]) + f" y {autores_corp[-1]}"
            else:
                autor_ref = autores_corp[0]
            autor_cita = autor_ref
        else:
            autor_ref = ""
            autor_cita = ""
    elif tipo_fuente == "Video / Multimedia":
        autor_ref = autor_raw
        autor_cita = autor_raw
    else:
        ref_autores, cita_autores = procesar_autores(autor_raw, formato_autor)
        autor_ref = formatear_autores_ref(ref_autores)
        autor_cita = formatear_autores_cita(cita_autores)

    match_anio = re.search(r'\d{4}', fecha)
    anio_cita = match_anio.group(0) if match_anio else "s. f."

    if autor_cita:
        cita_p.append((f"({autor_cita}, {anio_cita})", "normal"))
        cita_n.append((f"{autor_cita} ({anio_cita})", "normal"))
    else:
        cita_p.append((f"({titulo}, {anio_cita})", "normal"))
        cita_n.append((f"{titulo} ({anio_cita})", "normal"))

    if autor_ref:
        if autor_ref.endswith('.'):
            ref.append((f"{autor_ref} ", "normal"))
        else:
            ref.append((f"{autor_ref}. ", "normal"))
        ref.append((f"({fecha}). ", "normal"))
    else:
        ref.append((f"{titulo}. ", "italic" if tipo_fuente not in ["Revista Académica (Journal)"] else "normal"))
        ref.append((f"({fecha}). ", "normal"))

    if tipo_fuente == "Revista Académica (Journal)":
        if autor_ref: ref.append((f"{titulo}. ", "normal"))
        if revista:
            ref.append((f"{revista}", "italic"))
            if volumen: ref.append((f", {volumen}", "italic"))
            if numero: ref.append((f"({numero})", "normal"))
            if paginas: ref.append((f", {paginas}. ", "normal"))
            else: ref.append((". ", "normal"))
        else:
            ref.append((". ", "normal"))
    elif tipo_fuente == "Video / Multimedia":
        if autor_ref: ref.append((f"{titulo} ", "italic"))
        ref.append(("[Video]. ", "normal"))
        if sitio: ref.append((f"{sitio}. ", "normal"))
    elif tipo_fuente == "Noticia / Periódico":
        if autor_ref: ref.append((f"{titulo}. ", "italic"))
        if sitio: ref.append((f"{sitio}. ", "normal"))
    elif tipo_fuente == "Libro":
        if autor_ref: ref.append((f"{titulo}. ", "italic"))
        if editorial: ref.append((f"{editorial}. ", "normal"))
    else:
        if autor_ref: ref.append((f"{titulo}. ", "italic"))
        if sitio: ref.append((f"{sitio}. ", "normal"))

    if fecha_recuperacion:
        ref.append((f"Consultado el {fecha_recuperacion}. ", "normal"))
    
    if url:
        ref.append((url, "normal"))

    return {"referencia": ref, "cita_parentetica": cita_p, "cita_narrativa": cita_n}