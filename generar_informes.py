#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de informes HTML A4 — NI 2025 — GCBA/UEICEE
Paginación editorial por cantidad de salas + expansión visual por página.
"""
import re, os, sys
from pathlib import Path
from base64 import b64encode

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DATA_FILE  = "datos_para_informes_claude.txt"
OUTPUT_DIR = "informes_out"
IMG_HEADER = "image1.png"
IMG_FOOTER = "image2.png"

HBAR_H = 18.7
FBAR_H = 26.6
# Altura REAL del .pbody medida en el render (Playwright): 251.6mm.
# Se resta 10mm de reserva para la zona del número de página.
USABLE = 251.6   # alto real del cuerpo de página (.pbody clientHeight)

# Overhead fijo por tipo de página (mm), medido en el render real
PG_HDR_H   =  7.5   # estname-big (sin psub)
AT_H       =  8.0   # area-title pill (increased)
PG_OH      = PG_HDR_H + AT_H + 3   # +3mm de margen de seguridad

AVAIL_BLK  = USABLE - PG_OH    # ≈234mm disponibles para cuadros

# P1: intro + tabla Alfa (sin cuadros). Bigger table/title now ≈ 120mm.
P1_INTRO_H = 115.0
P1_AVAIL   = USABLE - P1_INTRO_H     # ≈132mm para cuadros en P1

# Primera pág Matemática: estname + area-title + tabla promedios + area-title.
# Medido real: estname 7.5 + at 6.5 + tabla 71 + at 6.5 ≈ 91.5mm de overhead.
MATE_P1_FIXED = PG_HDR_H + AT_H + 71.0 + AT_H + 3   # ≈97mm
MATE_P1_AVAIL = USABLE - MATE_P1_FIXED               # ≈157mm para cuadros

# Parámetros base de bloque (mm) — usados para escalar
BLK_BASE = dict(
    title_h      = 9.5,   # título a 9pt mínimo (piso legible)
    thead_h      = 6.5,   # thead a 8pt
    row_h        = 6.7,   # fila a 8.5pt
    note_lh      = 3.5,   # nota a 7.5pt por línea
    note_base    = 2.0,
    sep          = 4.0,   # separación generosa entre bloques
)
NIVEL4_LINES = {
    "Uso de la escritura":2,"Conciencia fonológica":3,"Correspondencias":4,
    "Lectura":1,"Escritura":3,"Comprensión":4,"Oralidad":4,"Vocabulario":4,
    "Espacio":2,"Figuras geométricas":1,"Situaciones aditivas":2,
    "Conteo":1,"Escritura de números":1,"Reconocimiento de números":1,"Serie numérica":1,
}

NIVEL_COLORS = {0:"#f2a99e",1:"#d44040",2:"#e0700f",3:"#f4c430",4:"#82c9a0"}

DIM_DISPLAY = {
    "Construcción de relatos":"Oralidad","Escritura - Ejecución":"Escritura",
    "Escritura - Uso":"Uso de la escritura","Palabras - Composición":"Conciencia fonológica",
    "Palabras - Reconocimiento":"Lectura","Relación Sonido - Palabra":"Correspondencias",
    "Textos - Representación":"Comprensión","Vocabulario":"Vocabulario",
    "Espacio":"Espacio","Formas geométricas":"Figuras geométricas",
    "Número - Adición":"Situaciones aditivas","Número - Cantidad":"Conteo",
    "Sist. Numérico - Escritura del número":"Escritura de números",
    "Sist. Numérico - Reconocimiento del número":"Reconocimiento de números",
    "Sist. Numérico - Serie":"Serie numérica",
}
DIM_DESC = {
    "Oralidad":"Relatar experiencias y participar en los intercambios de la sala.",
    "Escritura":"Escribir palabras simples y frecuentes.",
    "Uso de la escritura":"Reconocer el uso y las características de la escritura.",
    "Conciencia fonológica":"Reconocer que en las palabras se combinan unidades sonoras menores.",
    "Lectura":"Leer palabras simples y frecuentes.",
    "Correspondencias":"Relacionar los sonidos de las palabras con las letras que los representan.",
    "Comprensión":"Construir una representación mental coherente de los textos.",
    "Vocabulario":"Conocer el vocabulario en amplitud y profundidad.",
    "Espacio":"Utilizar relaciones espaciales para ubicar personas y objetos.",
    "Figuras geométricas":"Identificar las figuras geométricas y describir sus características.",
    "Situaciones aditivas":"Utilizar el número como recurso de anticipación para resolver situaciones aditivas.",
    "Conteo":"Contar colecciones de objetos.",
    "Escritura de números":"Escribir números de manera convencional.",
    "Reconocimiento de números":"Reconocer números en distintos portadores numéricos.",
    "Serie numérica":"Recitar la serie numérica.",
}
NIVEL4_DESC = {
    "Uso de la escritura":(
        "Comprende que la palabra impresa se organiza de forma diferente según los propósitos. "
        "Identifica partes y características del libro, como la portada y el título."),
    "Conciencia fonológica":(
        "Con orientación del/de la docente, identifica los sonidos en posición inicial y final, "
        "y comienza a distinguirlos en la posición intermedia en una palabra familiar. "
        "Con ayuda del/de la docente, puede identificar y contar cada uno de los sonidos en "
        "palabras familiares cortas (como 'sol')."),
    "Correspondencias":(
        "Distingue y recupera de manera consistente los sonidos de las letras trabajadas con el/la docente. "
        "Con orientación del/de la docente, identifica los sonidos de una palabra frecuente de una o dos "
        "sílabas y establece la correspondencia con letras móviles. "
        "Reconoce los sonidos de palabras simples (sol, sal) y les asigna las letras correspondientes."),
    "Lectura":"Con ayuda del/de la docente, lee palabras simples más extensas como luna, mano.",
    "Escritura":(
        "Escribe palabras simples de forma autónoma. "
        "Con ayuda del/de la docente, avanza en la escritura de palabras nuevas de dos sílabas "
        "con estructura simple como luna, mano, respetando la orientación de la escritura."),
    "Comprensión":(
        "Recupera oralmente secuencias de pasos cuando se brindan instrucciones. "
        "Renarra un cuento conocido recuperando personajes y eventos en orden cronológico. "
        "Responde preguntas sobre motivaciones y planes de los personajes. "
        "Formula y responde preguntas para relacionar el texto con sus conocimientos previos."),
    "Oralidad":(
        "Narra una secuencia de eventos y/o experiencias personales de manera organizada y clara. "
        "Formula preguntas para solicitar información y/o expandir su conocimiento. "
        "Participa de manera pertinente, aportando al tópico de la conversación. "
        "Reconoce, respeta y valora la diversidad lingüística de la sala."),
    "Vocabulario":(
        "Incorpora el vocabulario nuevo al volver a contar un relato o al recuperar información. "
        "Reconoce categorías de palabras y las utiliza con adecuación en diversos contextos. "
        "Con orientación del/de la docente, identifica palabras nuevas y reflexiona sobre su uso."),
    "Conteo":"Cuantifica colecciones de más de 19 elementos.",
    "Situaciones aditivas":(
        "Resuelve situaciones aditivas que involucran una reunión de partes con la incógnita "
        "en el total que se forma (más de 19 elementos)."),
    "Serie numérica":"Recita de manera autónoma la serie numérica hasta el 30 (o más).",
    "Reconocimiento de números":"Reconoce los números hasta el 30 (o más) en distintos portadores numéricos.",
    "Escritura de números":"Escribe de manera convencional los números hasta el 19 (o más).",
    "Espacio":(
        "Interpreta, comunica y representa gráficamente la posición de personas y objetos "
        "utilizando algunas referencias espaciales."),
    "Figuras geométricas":"Reconoce y describe de manera formal las características de tres o más figuras geométricas.",
}
ALFA_ORDER = ["Uso de la escritura","Correspondencias","Vocabulario","Oralidad",
              "Escritura","Conciencia fonológica","Comprensión","Lectura"]
MATE_ORDER = ["Espacio","Serie numérica","Conteo","Escritura de números",
              "Situaciones aditivas","Reconocimiento de números","Figuras geométricas"]


# ─────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────
def img_b64(path):
    try:
        d = b64encode(open(path,"rb").read()).decode()
        e = Path(path).suffix.lower().lstrip(".")
        m = {"png":"png","jpg":"jpeg","jpeg":"jpeg"}.get(e,"png")
        return f"data:image/{m};base64,{d}"
    except: return ""

def ensure_niv(d):
    for n in range(5): d.setdefault(n,(0,0.0))
    return d

PT2MM = 0.3528   # 1pt = 0.3528mm

def real_block_height(dim, n_rows, single, fe):
    """
    Altura REAL estimada de un bloque a un factor de expansión fe,
    replicando los tamaños que produce page_css().
    """
    if single:
        title_fs = min(11.0, 10.0*fe); td_fs = min(10.5, 9.5*fe)
        th_fs    = min(10.0,  9.0*fe); note_fs = min(9.0, 8.0*fe)
        cell_pd  = min( 3.2,  2.0*fe); blk_mb = min(8.0, 5.0*fe); note_lh = min(1.45, 1.30*fe)
        blk_mb_base = 5.0
    else:
        title_fs = max(9.0, min(10.5, 9.0*fe)); td_fs = max(8.5, min(10.0, 8.5*fe))
        th_fs    = max(8.0, min( 9.5, 8.0*fe)); note_fs = max(7.5, min(9.0, 7.5*fe))
        cell_pd  = min(2.8, 1.5*fe); blk_mb = min(6.0, 3.5*fe); note_lh = min(1.40, 1.28*fe)
    title_h = title_fs * 1.3 * PT2MM * 1.7 + 1.3     # ~1.7 líneas promedio de título
    thead_h = th_fs * 1.2 * PT2MM + 2*1.4
    row_h   = td_fs * note_lh * PT2MM + 2*cell_pd
    note_h  = NIVEL4_LINES.get(dim,2) * note_fs * note_lh * PT2MM + 1.8
    return title_h + thead_h + n_rows*row_h + note_h + blk_mb

def page_real_height(dims, n_rows, single, fe):
    return sum(real_block_height(d, n_rows, single, fe) for d in dims)

def blk_h(dim, n_rows, single=False):
    """Altura a factor 1.0 (piso mínimo legible)."""
    return real_block_height(dim, n_rows, single, 1.0)

def page_total_h(dims, n_rows, single=False):
    return sum(blk_h(d, n_rows, single) for d in dims)

def scale_factor(dims, n_rows, avail, single=False, fmax=2.0):
    """
    Busca (binaria) el mayor factor de expansión fe en [1.0, fmax] tal que
    la altura real de la página no exceda 'avail'. Nunca por debajo de 1.0
    (= piso mínimo legible), garantizado por las distribuciones editoriales.
    """
    if not dims:
        return 1.0
    if page_real_height(dims, n_rows, single, 1.0) > avail:
        return 1.0   # ni a piso entra (no debería ocurrir con distribuciones válidas)
    lo, hi = 1.0, fmax
    for _ in range(40):
        mid = (lo + hi) / 2
        if page_real_height(dims, n_rows, single, mid) <= avail:
            lo = mid
        else:
            hi = mid
    return lo


# ─────────────────────────────────────────────
# PAUTA EDITORIAL POR CANTIDAD DE SALAS
# Returns: list of page-specs
# Each spec: {"dims": [...], "area": "Alfa"|"Mate", "avail": mm, "is_mate_first": bool}
# ─────────────────────────────────────────────
def get_plan(n_salas):
    """Distribución editorial por cantidad de salas, validada a piso mínimo legible."""
    if n_salas == 1:
        return [
            {"area":"Alfa","dims":["Uso de la escritura"],"avail":P1_AVAIL,"p1":True},
            {"area":"Alfa","dims":["Correspondencias","Vocabulario","Oralidad","Escritura"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Conciencia fonológica","Comprensión","Lectura"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Espacio","Serie numérica"],"avail":MATE_P1_AVAIL,"mate_first":True},
            {"area":"Mate","dims":["Conteo","Escritura de números","Situaciones aditivas",
                                    "Reconocimiento de números","Figuras geométricas"],"avail":AVAIL_BLK},
        ]
    elif n_salas == 2:
        return [
            {"area":"Alfa","dims":["Uso de la escritura"],"avail":P1_AVAIL,"p1":True},
            {"area":"Alfa","dims":["Correspondencias","Vocabulario","Oralidad","Escritura"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Conciencia fonológica","Comprensión","Lectura"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Espacio","Serie numérica","Conteo"],"avail":MATE_P1_AVAIL,"mate_first":True},
            {"area":"Mate","dims":["Escritura de números","Situaciones aditivas","Reconocimiento de números","Figuras geométricas"],"avail":AVAIL_BLK},
        ]
    elif n_salas == 3:
        return [
            {"area":"Alfa","dims":[],"avail":P1_AVAIL,"p1":True},
            {"area":"Alfa","dims":["Uso de la escritura","Correspondencias","Vocabulario"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Oralidad","Escritura","Conciencia fonológica"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Comprensión","Lectura"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Espacio"],"avail":MATE_P1_AVAIL,"mate_first":True},
            {"area":"Mate","dims":["Serie numérica","Conteo","Escritura de números"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Situaciones aditivas","Reconocimiento de números","Figuras geométricas"],"avail":AVAIL_BLK},
        ]
    elif n_salas == 4:
        return [
            {"area":"Alfa","dims":[],"avail":P1_AVAIL,"p1":True},
            {"area":"Alfa","dims":["Uso de la escritura","Correspondencias","Vocabulario"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Oralidad","Escritura","Conciencia fonológica"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Comprensión","Lectura"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Espacio"],"avail":MATE_P1_AVAIL,"mate_first":True},
            {"area":"Mate","dims":["Serie numérica","Conteo","Escritura de números"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Situaciones aditivas","Reconocimiento de números","Figuras geométricas"],"avail":AVAIL_BLK},
        ]
    elif n_salas == 5:
        return [
            {"area":"Alfa","dims":[],"avail":P1_AVAIL,"p1":True},
            {"area":"Alfa","dims":["Uso de la escritura","Correspondencias","Vocabulario"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Oralidad","Escritura","Conciencia fonológica"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Comprensión","Lectura"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Espacio"],"avail":MATE_P1_AVAIL,"mate_first":True},
            {"area":"Mate","dims":["Serie numérica","Conteo","Escritura de números"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Situaciones aditivas","Reconocimiento de números","Figuras geométricas"],"avail":AVAIL_BLK},
        ]
    elif n_salas == 6:
        return [
            {"area":"Alfa","dims":[],"avail":P1_AVAIL,"p1":True},
            {"area":"Alfa","dims":["Uso de la escritura","Correspondencias","Vocabulario"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Oralidad","Escritura","Conciencia fonológica"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Comprensión","Lectura"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Espacio"],"avail":MATE_P1_AVAIL,"mate_first":True},
            {"area":"Mate","dims":["Serie numérica","Conteo","Escritura de números"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Situaciones aditivas","Reconocimiento de números","Figuras geométricas"],"avail":AVAIL_BLK},
        ]
    else:  # 7+
        # Cuadros muy altos (8+ filas): máximo 2 por página para legibilidad
        return [
            {"area":"Alfa","dims":[],"avail":P1_AVAIL,"p1":True},
            {"area":"Alfa","dims":["Uso de la escritura","Correspondencias"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Vocabulario","Oralidad"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Escritura","Conciencia fonológica"],"avail":AVAIL_BLK},
            {"area":"Alfa","dims":["Comprensión","Lectura"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":[],"avail":MATE_P1_AVAIL,"mate_first":True},
            {"area":"Mate","dims":["Espacio","Serie numérica"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Conteo","Escritura de números"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Situaciones aditivas","Reconocimiento de números"],"avail":AVAIL_BLK},
            {"area":"Mate","dims":["Figuras geométricas"],"avail":AVAIL_BLK},
        ]
# ─────────────────────────────────────────────
# CSS POR PÁGINA (scoped por clase)
# ─────────────────────────────────────────────
def page_css(cls, f, single=False):
    """
    Genera CSS scoped para una página.
    f >= 1.0  → expandir desde el piso de legibilidad (usa f como multiplicador).
    f <  1.0  → comprimir por debajo del piso (solo lo aplica el auto-fit cuando
                una página no entra ni siquiera al piso mínimo). Es excepcional.
    """
    fe = f

    if single:
        # Jardines de 1 sala: pisos generosos
        if fe >= 1.0:
            title_fs = round(min(11.0, 10.0 * fe), 2)
            td_fs    = round(min(10.5,  9.5 * fe), 2)
            th_fs    = round(min(10.0,  9.0 * fe), 2)
            tdagg_fs = round(min(10.5,  9.3 * fe), 2)
            note_fs  = round(min( 9.0,  8.0 * fe), 2)
            cell_pd  = round(min( 3.2,  2.0 * fe), 2)
            blk_mb   = round(min( 8.0,  5.0 * fe), 2)
            note_lh  = round(min(1.45, 1.30 * fe), 3)
        else:
            title_fs = round(10.0 * fe, 2); td_fs = round(9.5 * fe, 2)
            th_fs = round(9.0 * fe, 2); tdagg_fs = round(9.3 * fe, 2)
            note_fs = round(8.0 * fe, 2); cell_pd = round(2.0 * fe, 2)
            blk_mb = round(5.0 * fe, 2); note_lh = round(1.30 * fe, 3)
    else:
        # Multi-sala: pisos legibles
        if fe >= 1.0:
            title_fs = round(max(9.0,  min(10.5, 9.0 * fe)), 2)
            td_fs    = round(max(8.5,  min(10.0, 8.5 * fe)), 2)
            th_fs    = round(max(8.0,  min( 9.5, 8.0 * fe)), 2)
            tdagg_fs = round(max(8.3,  min( 9.8, 8.3 * fe)), 2)
            note_fs  = round(max(7.5,  min( 9.0, 7.5 * fe)), 2)
            cell_pd  = round(min(2.8, 1.5 * fe), 2)
            blk_mb   = round(min(7.0, 4.5 * fe), 2)
            note_lh  = round(min(1.40, 1.28 * fe), 3)
        else:
            title_fs = round(9.0 * fe, 2); td_fs = round(8.5 * fe, 2)
            th_fs = round(8.0 * fe, 2); tdagg_fs = round(8.3 * fe, 2)
            note_fs = round(7.5 * fe, 2); cell_pd = round(1.5 * fe, 2)
            blk_mb = round(4.5 * fe, 2); note_lh = round(1.28 * fe, 3)

    # Scale for combined-table and area-title too
    if fe >= 1.0:
        ct_fs  = round(min(10.5, 8.0 * fe), 2)
        ct_th  = round(min(10.0, 7.5 * fe), 2)
        ct_pd  = round(min(3.0, 1.3 * fe), 2)
        at_fs  = round(min(11.0, 10.0 * fe), 2)
    else:
        ct_fs  = round(max(6.5, 8.0 * fe), 2)
        ct_th  = round(max(6.0, 7.5 * fe), 2)
        ct_pd  = round(max(1.0, 1.3 * fe), 2)
        at_fs  = round(max(8.0, 10.0 * fe), 2)

    return f"""
.{cls} .dim-block {{ margin-bottom:{blk_mb}mm; }}
.{cls} .dim-title {{ font-size:{title_fs}pt; }}
.{cls} .lvl-table {{ font-size:{td_fs}pt; }}
.{cls} .lvl-table th {{ font-size:{th_fs}pt; padding:{cell_pd}mm 1.5mm; }}
.{cls} .lvl-table td {{ font-size:{td_fs}pt; padding:{cell_pd}mm 1.5mm; }}
.{cls} .lvl-table td.td-agg {{ font-size:{tdagg_fs}pt; }}
.{cls} .dim-note {{ font-size:{note_fs}pt; line-height:{note_lh}; }}
.{cls} .combined-table {{ font-size:{ct_fs}pt; }}
.{cls} .combined-table th {{ font-size:{ct_th}pt; padding:{ct_pd}mm 2mm; }}
.{cls} .combined-table td {{ padding:{ct_pd}mm 2mm; }}
.{cls} .ct-desc {{ font-size:{round(max(6.5, ct_fs * 0.92), 2)}pt; }}
.{cls} .ct-content {{ font-size:{ct_fs}pt; }}
.{cls} .area-title {{ font-size:{at_fs}pt; }}
"""


# ─────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────
def parse_data_file(filepath):
    text = open(filepath,encoding="utf-8").read()
    results = []
    for raw in re.split(r"={70}\nESTABLECIMIENTO:",text)[1:]:
        name = raw.split("\n")[0].strip()
        ta   = {}
        m = re.search(r"### Materia:\s+Matemática\s*\nMatrícula Total Evaluada en el Jardín:\s+(\d+)",raw)
        if m: ta["Matemática"]=int(m.group(1))
        m = re.search(r"### Materia:\s+Lengua\s*\nMatrícula Total Evaluada en el Jardín:\s+(\d+)",raw)
        if m: ta["Alfabetización"]=int(m.group(1))

        salas=[]
        for sb in re.split(r"-{70}\nSALITA:",raw)[1:]:
            m=re.match(r"\s*(.*?)\s+\(ID:\s+(\d+)\s*\)",sb.split("\n")[0])
            if not m: continue
            sdims={"Alfabetización":{},"Matemática":{}}; smat={"Alfabetización":0,"Matemática":0}
            for ab in re.split(r"#### >> Área:",sb)[1:]:
                ah=ab.split("\n")[0]
                ak=("Alfabetización" if "Lengua" in ah else "Matemática" if "Matemática" in ah else None)
                if not ak: continue
                mm=re.search(r"Matrícula en salita:\s+(\d+)",ah)
                if mm: smat[ak]=int(mm.group(1))
                for db in re.split(r"\* Dimensión:",ab)[1:]:
                    dl=db.split("\n")
                    mm2=re.match(r"\s*(.*?)\s+\(Total respuestas:\s+(\d+)\s*\)",dl[0])
                    if not mm2: continue
                    disp=DIM_DISPLAY.get(mm2.group(1).strip())
                    if not disp: continue
                    niv={}; in_t=hdr=sep=False
                    for line in dl[1:]:
                        if line.startswith("  |") or line.startswith("| "):
                            s=line.strip()
                            if not in_t: in_t=hdr=True; continue
                            if hdr and not sep: sep=True; continue
                            pts=[p.strip() for p in s.split("|") if p.strip()]
                            if len(pts)>=2:
                                al=int(pts[1]) if pts[1].isdigit() else 0
                                try: pct=float(pts[2].rstrip("%")) if len(pts)>2 else 0.0
                                except: pct=0.0
                                nm=re.search(r"Nivel\s+(\d+)",pts[0],re.IGNORECASE)
                                nv=int(nm.group(1)) if nm else (0 if "previo" in pts[0].lower() else None)
                                if nv is not None: niv[nv]=(al,pct)
                        elif in_t: break
                    sdims[ak][disp]=ensure_niv(niv)
            salas.append({"name":m.group(1).strip(),"matricula":smat,"dims":sdims})
        if salas: results.append({"name":name,"total_alumnos":ta,"salas":salas})
    return results

def compute_totals(salas,area,dims):
    t={}
    for d in dims:
        c={n:0 for n in range(5)}
        for s in salas:
            for n in range(5): c[n]+=s["dims"][area].get(d,{}).get(n,(0,0))[0]
        tot=sum(c.values())
        t[d]={n:(c[n],c[n]/tot*100 if tot else 0.) for n in range(5)}
    return t

def avg(ddata,n): return 0. if not n else sum(i*ddata.get(i,(0,0))[0] for i in range(5))/n


# ─────────────────────────────────────────────
# CSS BASE
# ─────────────────────────────────────────────
HBAR_B64=FBAR_B64=""
BASE_CSS = f"""
* {{ -webkit-print-color-adjust:exact !important; print-color-adjust:exact !important;
     color-adjust:exact !important; box-sizing:border-box; margin:0; padding:0; }}
:root {{ --yellow:#FFCC00; --navy:#153244; --cyan:#8DE2D6; --cyan-dark:#5bc4ba;
         --soft:#eef8f7; --line:#d8e2e7; --muted:#5c6670; }}
body {{ font-family:"Archivo",Arial,sans-serif; background:#e0e0e0; color:var(--navy); line-height:1.4; }}
.page {{ width:210mm; height:297mm; margin:0 auto 8mm; background:#fff;
         display:flex; flex-direction:column; page-break-after:always; break-after:page;
         position:relative; overflow:hidden; }}
.hbar {{ width:210mm; height:{HBAR_H}mm; flex-shrink:0;
         background-size:100% 100%; background-repeat:no-repeat; }}
.fbar {{ width:210mm; height:{FBAR_H}mm; flex-shrink:0;
         background-size:100% 100%; background-repeat:no-repeat; }}
.pbody {{ flex:1; padding:4mm 11mm 3mm; overflow:hidden; }}
.fpage {{ position:absolute; right:15mm; bottom:31mm; display:flex; align-items:center; gap:1.3mm; z-index:10; }}
.fpage .fp-bar {{ width:1.8mm; height:3.8mm; background:var(--yellow); border-radius:1px; display:inline-block; }}
.fpage .fp-num  {{ font-size:9.5pt; font-weight:800; color:var(--navy); line-height:1; }}
.ueicee-pill {{ display:inline-block; background:var(--navy); color:#fff; font-size:7.5pt;
               font-weight:700; letter-spacing:.04em; padding:1.5mm 4mm;
               border-radius:999px; margin-bottom:2.5mm; }}
.estname-big {{ display:flex; align-items:center; gap:3mm; font-size:13.5pt; font-weight:800;
                color:var(--navy); line-height:1.15; margin-bottom:0.8mm; }}
.estname-big .pm-bar {{ width:2.5mm; height:7.5mm; background:var(--yellow); border-radius:1px; flex-shrink:0; }}
.ptitle {{ font-size:10pt; font-weight:700; color:var(--navy); line-height:1.2; margin-bottom:1.5mm; }}
.sum-pill {{ display:inline-flex; align-items:center; background:var(--yellow);
             color:var(--navy); padding:1.5mm 4mm; border-radius:2mm;
             font-size:10pt; font-weight:800; margin-right:3mm; }}
.intro-box {{ background:var(--soft); border:1.5px solid var(--cyan); border-radius:3mm; padding:3.5mm 5.5mm; margin-top:2.5mm; }}
.intro-kicker {{ font-size:9.5pt; font-weight:800; color:var(--navy); letter-spacing:.06em;
                 text-transform:uppercase; margin-bottom:2.5mm;
                 border-bottom:2px solid var(--cyan); padding-bottom:1.5mm; }}
.intro-body {{ font-size:9.5pt; color:var(--navy); line-height:1.3; margin-bottom:1.5mm; }}
.intro-list {{ padding-left:5mm; margin:0; }}
.intro-list li {{ font-size:9.5pt; color:var(--navy); line-height:1.3; margin-bottom:1mm; }}
.area-title {{ font-size:10pt; font-weight:800; color:var(--navy); margin-bottom:2.5mm;
               padding:2mm 4mm; background:var(--soft);
               border-left:4px solid var(--cyan-dark); border-radius:1mm; }}
.combined-table {{ width:100%; border-collapse:collapse; font-size:8pt; margin-bottom:5mm; }}
.combined-table th {{ background:var(--navy); color:#fff; padding:1.8mm 2mm; font-size:8pt;
                      font-weight:700; vertical-align:bottom; line-height:1.2; text-align:left; }}
.combined-table td {{ padding:1.3mm 2mm; border-bottom:1px solid var(--line);
                      vertical-align:middle; line-height:1.2; color:var(--navy); }}
.combined-table tbody tr:nth-child(even) td {{ background:#f5fafa; }}
.ct-content {{ font-weight:700; font-size:8.5pt; }} .ct-desc {{ color:var(--muted)!important; font-size:8.5pt; }}
.ct-score {{ text-align:center!important; font-weight:700; font-size:9.5pt; }}
.ct-total-col {{ background:var(--yellow)!important; }}
.combined-table th.ct-total-col {{ color:#fff!important; }}
.combined-table td.ct-total-col {{ color:#fff!important; font-weight:800!important; }}
/* Base dim-block — overridden per-page by scoped CSS */
.dim-block {{ margin-bottom:5.5mm; page-break-inside:avoid; }}
.dim-title {{ font-size:9pt; font-weight:400; color:var(--navy); margin-bottom:1.5mm; line-height:1.3; }}
.dim-title strong {{ font-weight:800; }}
.lvl-table {{ width:100%; border-collapse:collapse; font-size:8.5pt; }}
.lvl-table th {{ background:var(--navy); color:#fff; text-align:center; font-size:8pt;
                 font-weight:700; padding:1.6mm 1.5mm; line-height:1.2; }}
.lvl-table th.lth-agg {{ text-align:left; min-width:42mm; }}
.lvl-table td {{ padding:1.6mm 1.5mm; text-align:center; font-weight:600; color:var(--navy);
                 font-size:8.5pt; line-height:1.15; border-bottom:1px solid rgba(0,0,0,.08); }}
.lvl-table td.td-agg {{ text-align:left; font-weight:700; font-size:8.3pt; color:var(--navy);
                         background:#f0f4f5!important; border-bottom:1px solid var(--line);
                         white-space:nowrap; }}
.lvl-table tr.tr-total td {{ font-weight:800; }}
.lvl-table tr.tr-total td.td-agg {{ background:var(--yellow)!important; color:var(--navy)!important; }}
.dim-note {{ font-size:7.5pt; color:var(--muted); margin-top:1.2mm; line-height:1.3; padding-left:1mm; }}
.dim-note strong {{ color:var(--navy); font-weight:700; }}
@media print {{ body {{ background:#fff; }} .page {{ margin:0; box-shadow:none; }} }}
@page {{ size:210mm 297mm; margin:0; }}
"""


# ─────────────────────────────────────────────
# HTML BUILDERS
# ─────────────────────────────────────────────
def pw(cls, content, pnum):
    return (f'<div class="page {cls}">'
            f'<div class="hbar" style="background-image:url(\'{HBAR_B64}\');"></div>'
            f'<div class="pbody">{content}</div>'
            f'<div class="fbar" style="background-image:url(\'{FBAR_B64}\');"></div>'
            f'<div class="fpage"><span class="fp-bar"></span>'
            f'<span class="fp-num">{pnum}</span></div></div>')

def hdr(name,ue=False):
    u=('<div class="ueicee-pill">UEICEE (UNIDAD DE EVALUACIÓN INTEGRAL DE LA CALIDAD Y EQUIDAD EDUCATIVA)</div>'
       if ue else "")
    return f'{u}<div class="estname-big"><span class="pm-bar"></span><span>{name}</span></div>'

def subhdr(name,area):
    # El subtítulo .psub redundante se elimina; solo se muestra el nombre del jardín.
    return hdr(name)

def at(txt):
    return f'<div class="area-title">{txt}</div>'

def nivel_cell(al,pct,n):
    return f'<td style="background:{NIVEL_COLORS[n]};">{al} ({round(pct):.0f}%)</td>'

def dim_blk(dim, tot_dim, salas, single):
    desc = DIM_DESC.get(dim,"")
    note = NIVEL4_DESC.get(dim,"")
    title = f'<div class="dim-title"><strong>{dim}:</strong> {desc}</div>'
    thead = ('<table class="lvl-table"><thead><tr>'
             '<th class="lth-agg">Niveles</th>'
             '<th>Nivel 0</th><th>Nivel 1</th><th>Nivel 2</th><th>Nivel 3</th><th>Nivel 4</th>'
             '</tr></thead><tbody>')
    rows=[]
    if not single:
        cells="".join(nivel_cell(tot_dim.get(n,(0,0))[0],tot_dim.get(n,(0,0))[1],n) for n in range(5))
        rows.append(f'<tr class="tr-total"><td class="td-agg">Total jardín</td>{cells}</tr>')
    for s in salas:
        ar=next((a for a in ("Alfabetización","Matemática") if dim in s["dims"].get(a,{})),None)
        d=s["dims"].get(ar,{}).get(dim,ensure_niv({})) if ar else ensure_niv({})
        cells="".join(nivel_cell(d.get(n,(0,0))[0],d.get(n,(0,0))[1],n) for n in range(5))
        sn=s["name"]
        rows.append(f'<tr><td class="td-agg">{sn}</td>{cells}</tr>')
    nh=(f'<div class="dim-note"><strong>Nivel 4 esperado según DC:</strong> {note}</div>'
        if note else "")
    return f'<div class="dim-block">{title}{thead}{"".join(rows)}</tbody></table>{nh}</div>'

def avg_tbl(salas,area,dims,tots,single):
    if single:
        sths=f'<th class="ct-score" style="width:20mm;font-size:7.5pt;">{salas[0]["name"]}</th>'
    else:
        sths="".join(f'<th class="ct-score" style="width:18mm;font-size:7.5pt;">{s["name"]}</th>' for s in salas)
    tth=('' if single else '<th class="ct-score ct-total-col" style="width:17mm;">Total jardín</th>')
    head=(f'<thead><tr><th style="width:28mm;">Contenido</th><th>Descripción</th>'
          f'{tth}{sths}</tr></thead>')
    rows=[]
    for d in dims:
        td=tots.get(d,{}); tn=sum(td.get(n,(0,0))[0] for n in range(5)); ta=avg(td,tn)
        ttd=('' if single else f'<td class="ct-score ct-total-col">{ta:.2f}</td>')
        stds="".join(f'<td class="ct-score">{avg(s["dims"][area].get(d,{}),s["matricula"].get(area,0)):.2f}</td>' for s in salas)
        rows.append(f'<tr><td class="ct-content">{d}</td><td class="ct-desc">{DIM_DESC.get(d,"")}</td>{ttd}{stds}</tr>')
    return f'<table class="combined-table">{head}<tbody>{"".join(rows)}</tbody></table>'


# ─────────────────────────────────────────────
# BUILD REPORT
# ─────────────────────────────────────────────
def build_report(est, factor_overrides=None):
    """
    factor_overrides: dict {cls: factor} para forzar el factor de escala de
    páginas específicas (usado por el auto-fit con render real).
    """
    name   = est["name"]
    salas  = est["salas"]
    ns     = len(salas)
    single = (ns == 1)
    n_rows = 1 if single else (1+ns)
    factor_overrides = factor_overrides or {}

    ta_alfa = est["total_alumnos"].get("Alfabetización") or (salas[0]["matricula"].get("Alfabetización",0) if salas else 0)

    tots_a = compute_totals(salas,"Alfabetización",ALFA_ORDER)
    tots_m = compute_totals(salas,"Matemática",MATE_ORDER)

    plan   = get_plan(ns)
    pages  = []
    pnum   = 1
    scoped_css = []

    # Nombre de sala para el informe
    sw = "sala" if ns==1 else "salas"

    for spec in plan:
        dims      = spec["dims"]
        area      = spec["area"]
        avail     = spec["avail"]
        is_p1     = spec.get("p1", False)
        is_mf     = spec.get("mate_first", False)
        cls       = f"pg{pnum}"

        # Factor de escala para esta página (override del auto-fit si existe)
        if cls in factor_overrides:
            f = factor_overrides[cls]
        else:
            f = scale_factor(dims, n_rows, avail, single=single) if dims else 1.0
        scoped_css.append(page_css(cls, f, single=single))

        # Ajuste condicional para tablas de promedios en P1 (5+ salas)
        if is_p1 and ns >= 5:
            if ns >= 7:
                # 7+ salas: corregir jerarquía tipográfica + comprimir más
                scoped_css.append(f"""
.{cls} .area-title {{ font-size:9pt; padding:1.5mm 3mm; }}
.{cls} .combined-table th {{ font-size:7.5pt; padding:1.0mm 1.5mm; }}
.{cls} .ct-content {{ font-size:7.5pt; }}
.{cls} .ct-desc {{ font-size:7pt; }}
.{cls} .ct-score {{ font-size:6.5pt !important; }}
.{cls} .combined-table td {{ padding:0.8mm 1.5mm; line-height:1.1; }}
.{cls} .combined-table {{ margin-bottom:0.5mm; }}
""")
            elif ns == 6:
                # 6 salas: reducir ~1cm con fonts levemente menores
                scoped_css.append(f"""
.{cls} .combined-table th {{ padding:1.2mm 2mm; }}
.{cls} .combined-table td {{ padding:1.0mm 2mm; }}
.{cls} .ct-content {{ font-size:8.8pt !important; }}
.{cls} .ct-desc {{ font-size:8pt !important; }}
.{cls} .ct-score {{ font-size:8pt !important; }}
.{cls} .combined-table {{ margin-bottom:1mm; }}
""")
            else:
                # 5 salas: reducir ~1cm con fonts levemente menores
                scoped_css.append(f"""
.{cls} .combined-table td {{ padding:1.2mm 2mm; }}
.{cls} .ct-content {{ font-size:10pt !important; }}
.{cls} .ct-desc {{ font-size:9pt !important; }}
.{cls} .combined-table {{ margin-bottom:1mm; }}
""")

        if is_p1:
            # Página 1: intro + tabla Alfa + cuadros opcionales
            content = (
                hdr(name,ue=True)
                + f'<div class="ptitle">Resultados de la Evaluación "Alfabetización y Matemática - Sala de 5 años"</div>'
                + f'<div style="margin:2mm 0 2.5mm;"><span class="sum-pill">{ta_alfa} niños evaluados</span>'
                + f'<span class="sum-pill">{ns} {sw}</span></div>'
                + '<div class="intro-box"><div class="intro-kicker">INTRODUCCIÓN</div>'
                + '<div class="intro-body">Con la intención de ofrecer información para la mejora de los '
                + 'aprendizajes y la enseñanza en el nivel inicial, se presentan los resultados obtenidos '
                + 'por el establecimiento en la evaluación de aprendizajes de '
                + '<strong>Alfabetización y Matemática en niños de 5 años - 2025</strong>.<br><br>'
                + 'Los resultados se brindan para el total del jardín y por sala, considerando para cada área:'
                + '<ul class="intro-list">'
                + '<li><strong>Puntaje promedio</strong> del conjunto de niños en cada contenido evaluado: <strong>0 a 4 puntos</strong></li>'
                + '<li><strong>Nivel de logro</strong> en el que se ubican los niños en cada contenido: del <strong>0 (nivel previo)</strong> al <strong>4 (meta del DC)</strong>.</li>'
                + '</ul></div></div>'
                + f'<div style="margin-top:{6 if ns >= 3 else 2.5}mm;">'
                + at("Alfabetización: puntaje promedio por contenido.")
                + avg_tbl(salas,"Alfabetización",ALFA_ORDER,tots_a,single)
                + '</div>'
            )
            if dims:
                content += at("Alfabetización: nivel de logro en cada contenido.")
                content += "".join(dim_blk(d,tots_a.get(d,ensure_niv({})),salas,single) for d in dims)

        elif is_mf:
            # Primera página de Matemática: tabla + cuadros (si hay)
            content = (
                subhdr(name,"Matemática")
                + at("Matemática: puntaje promedio por contenido.")
                + avg_tbl(salas,"Matemática",MATE_ORDER,tots_m,single)
            )
            if dims:
                content += at("Matemática: nivel de logro en cada contenido.")
                content += "".join(dim_blk(d,tots_m.get(d,ensure_niv({})),salas,single) for d in dims)

        else:
            # Página de cuadros pura (Alfa o Mate)
            tots = tots_a if area=="Alfa" else tots_m
            at_txt = ("Alfabetización: nivel de logro en cada contenido."
                      if area=="Alfa" else "Matemática: nivel de logro en cada contenido.")
            content = (
                subhdr(name, "Alfabetización" if area=="Alfa" else "Matemática")
                + at(at_txt)
                + "".join(dim_blk(d,tots.get(d,ensure_niv({})),salas,single) for d in dims)
            )

        pages.append(pw(cls, content, pnum))
        pnum += 1

    all_scoped = "\n".join(scoped_css)
    return (f'<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">'
            f'<title>Informe - {name}</title>'
            f'<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700;800;900&display=swap" rel="stylesheet">'
            f'<style>{BASE_CSS}\n{all_scoped}</style></head><body>'
            f'{"".join(pages)}</body></html>')


# ─────────────────────────────────────────────
# AUTO-FIT CON RENDER REAL (Playwright)
# ─────────────────────────────────────────────
def _measure_overflow(html):
    """
    Renderiza el HTML en un navegador headless y devuelve, por cada página,
    el overflow en mm (scrollHeight - clientHeight del .pbody) y su clase.
    Retorna lista [(cls, overflow_mm), ...].
    """
    import tempfile, asyncio
    from playwright.async_api import async_playwright

    async def run():
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
            tf.write(html); path = tf.name
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{path}")
            data = await page.evaluate("""() => {
                const PX2MM = 25.4/96;
                const out = [];
                document.querySelectorAll('.page').forEach(pg => {
                    const body = pg.querySelector('.pbody');
                    if (!body) return;
                    const cls = [...pg.classList].find(c => c.startsWith('pg')) || '';
                    out.push({cls: cls, overflow: (body.scrollHeight - body.clientHeight) * PX2MM});
                });
                return out;
            }""")
            await browser.close()
        os.unlink(path)
        return [(d["cls"], d["overflow"]) for d in data]

    return asyncio.run(run())


def autofit_report(est, max_iters=20):
    """
    Ajusta el factor de escala de cada página midiendo el render real, buscando
    para cada página el MAYOR factor que no produce overflow (máxima legibilidad).
    Estrategia: por página, mantenemos una cota inferior (sin overflow conocido)
    y superior (con overflow conocido) y hacemos bisección sobre el render real.
    """
    ns = len(est["salas"]); single = (ns == 1)

    # Factor inicial por página (el que scale_factor propone, capeado a un techo)
    plan = get_plan(ns)
    n_pages = len(plan)
    cls_list = [f"pg{i+1}" for i in range(n_pages)]

    # Estado de bisección por página: lo (sin overflow), hi (con overflow o None)
    lo = {c: None for c in cls_list}   # mayor factor sin overflow conocido
    hi = {c: None for c in cls_list}   # menor factor con overflow conocido
    cur = {}
    for i, spec in enumerate(plan):
        c = cls_list[i]
        cur[c] = _factor_for_cls(est, c) if spec["dims"] else 2.0

    html = build_report(est, factor_overrides=cur)

    for _ in range(max_iters):
        measures = dict(_measure_overflow(html))
        any_over = False
        for c in cls_list:
            ov = measures.get(c, 0.0)
            if ov > 0.2:
                any_over = True
                hi[c] = cur[c]                     # este factor desborda
                if lo[c] is not None:
                    cur[c] = round((lo[c] + hi[c]) / 2, 4)   # bisección
                else:
                    # bajar con paso proporcional al exceso
                    step = max(0.05, ov / 110.0)
                    cur[c] = round(max(0.35, cur[c] - step), 4)
            else:
                # sin overflow: registrar como cota inferior y tratar de subir
                if lo[c] is None or cur[c] > lo[c]:
                    lo[c] = cur[c]
                if hi[c] is not None and (hi[c] - lo[c]) > 0.02:
                    cur[c] = round((lo[c] + hi[c]) / 2, 4)   # subir hacia el óptimo
        if not any_over and all(
            (hi[c] is None or (lo[c] is not None and (hi[c]-lo[c]) <= 0.02))
            for c in cls_list
        ):
            break
        html = build_report(est, factor_overrides=cur)

    # Asegurar build final con los factores sin overflow (usar lo[] si existe)
    final_factors = {c: (lo[c] if lo[c] is not None else cur[c]) for c in cls_list}
    html = build_report(est, factor_overrides=final_factors)

    # Páginas bajo piso de legibilidad
    bajo_piso = set()
    base_td = 9.5 if single else 8.5
    for c, fac in final_factors.items():
        if base_td * fac < base_td - 0.01:   # fac < 1.0 → por debajo del piso
            bajo_piso.add(c)

    return html, final_factors, bajo_piso


def _factor_for_cls(est, target_cls):
    """Reconstruye el factor que scale_factor asignaría a una página por su clase."""
    ns = len(est["salas"]); single = (ns == 1); n_rows = 1 if single else 1+ns
    plan = get_plan(ns)
    for i, spec in enumerate(plan, 1):
        if f"pg{i}" == target_cls:
            dims = spec["dims"]
            if not dims:
                return 1.0
            return scale_factor(dims, n_rows, spec["avail"], single=single)
    return 1.0


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    global HBAR_B64, FBAR_B64
    HBAR_B64=img_b64(IMG_HEADER); FBAR_B64=img_b64(IMG_FOOTER)
    os.makedirs(OUTPUT_DIR,exist_ok=True)
    filter_names=[a.strip().lower() for a in sys.argv[1:]] if len(sys.argv)>1 else []
    print(f"Parseando {DATA_FILE}...")
    ests=parse_data_file(DATA_FILE)
    print(f"  -> {len(ests)} jardines encontrados")
    generated=0
    for est in ests:
        name=est["name"]
        if filter_names and not any(f in name.lower() for f in filter_names): continue
        ns=len(est["salas"])
        print(f"  {name} ({ns} sala(s))...", end=" ", flush=True)
        try:
            html, overrides, bajo_piso = autofit_report(est)
        except Exception as e:
            print(f"ERROR: {e}"); import traceback; traceback.print_exc(); continue
        # Verificación final de overflow
        final = _measure_overflow(html)
        bad = [(c,o) for c,o in final if o > 0.8]
        status = "OK" if not bad else f"OVERFLOW en {len(bad)} pág"
        if bajo_piso:
            status += f" (·{len(bajo_piso)} pág bajo piso de legibilidad)"
        print(status)
        safe=re.sub(r'[\\/:*?"<>|]',"_",name).strip()
        open(os.path.join(OUTPUT_DIR,f"Informe_{safe}.html"),"w",encoding="utf-8").write(html)
        generated+=1
    print(f"\n-> {generated} informe(s) en '{OUTPUT_DIR}/'")

if __name__=="__main__": main()
