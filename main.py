import os
import fitz  
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import json

def es_autor_valido(texto):
    if not texto or not isinstance(texto, str): return False
    texto_lower = texto.strip().lower()
    if texto_lower.startswith('http://') or texto_lower.startswith('https://') or texto_lower.startswith('www.'): return False
    if 'wikimedia' in texto_lower or 'wikipedia' in texto_lower: return False
    basura_pdf = ['microsoft', 'word', 'acrobat', 'writer', 'pdf', 'hp', 'usuario']
    for palabra in basura_pdf:
        if palabra in texto_lower: return False
    return True

def extraer_metadatos_pdf(doc, origen):
    meta = doc.metadata
    titulo = meta.get("title", "").strip()
    autor = meta.get("author", "").strip()
    fecha = "s.f."
    match = re.search(r'D:(\d{4})', meta.get("creationDate", ""))
    if match: fecha = match.group(1)

    if len(doc) > 0:
        texto_pag1 = doc[0].get_text("text")
        lineas = [linea.strip() for linea in texto_pag1.split('\n') if linea.strip()]
        
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
                titulo = nombre_base.replace('-', ' ').replace('_', ' ').strip().capitalize()

        if not autor or not es_autor_valido(autor):
            for linea in lineas:
                match_aut = re.search(r'(?i)^(alumno|autor|estudiante|nombre)\s*:\s*(.*)', linea)
                if match_aut and match_aut.group(2):
                    autor = match_aut.group(2).strip().title()
                    break
                    
        if fecha == "s.f.":
            match_fecha = re.search(r'\b(20\d{2})\b', texto_pag1)
            if match_fecha: fecha = match_fecha.group(1)

    tipo_fuente = "Página Web / Documento Genérico"
    if "dialnet" in origen.lower() or "redalyc" in origen.lower():
        tipo_fuente = "Revista Académica (Journal)"

    return {
        'url': origen, 'autor': autor if es_autor_valido(autor) else None,
        'titulo': titulo if titulo else "Sin título", 'fecha': fecha,
        'sitio': None, 'revista': '', 'volumen': '', 'numero': '', 'paginas': '',
        'tipo_fuente_sugerido': tipo_fuente
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
        'url': entrada, 'autor': None, 'titulo': None, 'fecha': "s.f.",
        'sitio': None, 'revista': '', 'volumen': '', 'numero': '', 'paginas': '',
        'tipo_fuente_sugerido': "Página Web / Documento Genérico"
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

    meta_author = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', attrs={'name': 'citation_author'})
    og_author = soup.find('meta', property='article:author')
    if meta_author and es_autor_valido(meta_author.get('content')): metadatos['autor'] = meta_author['content'].strip()
    elif og_author and es_autor_valido(og_author.get('content')): metadatos['autor'] = og_author['content'].strip()

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
    if meta_yt_date and meta_yt_date.get('content') and metadatos['fecha'] == "s.f.":
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
                            if autores_limpios: metadatos['autor'] = ", ".join(autores_limpios)

                        fecha_str = nodo.get('dateModified') or nodo.get('datePublished')
                        if fecha_str and metadatos['fecha'] == "s.f.":
                            m = re.search(r'\d{4}', fecha_str)
                            if m: metadatos['fecha'] = m.group(0)
        except json.JSONDecodeError: continue

    if metadatos['fecha'] == "s.f.":
        og_pub = soup.find('meta', property='article:published_time') or soup.find('meta', attrs={'name': 'citation_publication_date'})
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
        
    return metadatos

def generar_cita_apa(datos, tipo_fuente, fecha_recuperacion=""):
    cita = []
    autor = datos.get('autor')
    sitio = datos.get('sitio')
    titulo = datos.get('titulo', 'Sin título')
    fecha = datos.get('fecha', 's.f.')
    url = datos.get('url', '') if str(datos.get('url', '')).startswith('http') else ""
    
    revista = datos.get('revista', '')
    volumen = datos.get('volumen', '')
    numero = datos.get('numero', '')
    paginas = datos.get('paginas', '')

    if 'wikipedia.org' in url.lower():
        cita.append((f"{titulo}. ", "italic"))
        cita.append((f"({fecha}). En Wikipedia. ", "normal"))
        if url: cita.append((url, "normal"))
        return cita

    if not autor and sitio:
        autor = sitio
        sitio = ""

    if autor:
        cita.append((f"{autor}. ", "normal"))
        cita.append((f"({fecha}). ", "normal"))

    if tipo_fuente == "Revista Académica (Journal)":
        if not autor:
            cita.append((f"{titulo}. ", "normal"))
            cita.append((f"({fecha}). ", "normal"))
        else:
            cita.append((f"{titulo}. ", "normal"))
            
        if revista:
            cita.append((f"{revista}", "italic"))
            if volumen: cita.append((f", {volumen}", "italic"))
            if numero: cita.append((f"({numero})", "normal"))
            if paginas: cita.append((f", {paginas}. ", "normal"))
            else: cita.append((". ", "normal"))
        else:
            cita.append((". ", "normal"))

    elif tipo_fuente == "Video / Multimedia":
        if not autor:
            cita.append((f"{titulo} ", "italic"))
            cita.append(("[Video]. ", "normal"))
            cita.append((f"({fecha}). ", "normal"))
        else:
            cita.append((f"{titulo} ", "italic"))
            cita.append(("[Video]. ", "normal"))
        
        if sitio: cita.append((f"{sitio}. ", "normal"))

    elif tipo_fuente == "Noticia / Periódico":
        if not autor:
            cita.append((f"{titulo}. ", "italic"))
            cita.append((f"({fecha}). ", "normal"))
        else:
            cita.append((f"{titulo}. ", "italic"))
        
        if sitio: cita.append((f"{sitio}. ", "normal"))

    else: 
        if not autor:
            cita.append((f"{titulo}. ", "italic"))
            cita.append((f"({fecha}). ", "normal"))
        else:
            cita.append((f"{titulo}. ", "italic"))
            
        if sitio: cita.append((f"{sitio}. ", "normal"))

    if fecha_recuperacion:
        cita.append((f"Recuperado el {fecha_recuperacion}, de ", "normal"))
    
    if url:
        cita.append((url, "normal"))

    return cita