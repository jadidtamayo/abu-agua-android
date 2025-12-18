import re
from typing import List, Dict, Optional, Tuple

def limpiar_texto(texto: str) -> str:
    texto = re.sub(r'\s+', ' ', texto)
    
    footer_patterns = [
        r'Estimado Cliente el pago de la factura.*',
        r'TRANSFERMOVIL.*',
        r'Ante dudas deberá comunicarse.*'
    ]
    for pattern in footer_patterns:
        texto = re.sub(pattern, '', texto, flags=re.IGNORECASE)
        
    return texto.strip()

def extraer_fecha(texto: str) -> Optional[str]:
    match = re.search(r'(\d{1,2}/\d{1,2})', texto)
    return match.group(1) if match else None

def extraer_infraestructura(nota: str) -> Tuple[Optional[str], str]:
    """
    Given a note string, extracts the likely infrastructure name and the rest of the note.
    Strategies:
    1. Everything before "con servicio", "sin servicio", "ya terminó", etc. is likely the Name.
    2. Everything else is the Info/Status.
    """
    separators_pattern = r'\s+(?:con servicio|sin servicio|ya terminó|terminó|termino|se planifica|servicio para|servicio)\b'
    
    parts = re.split(separators_pattern, nota, maxsplit=1, flags=re.IGNORECASE)
    
    nombre_raw = parts[0]
    # The 'split' consumes the separator, so we need to find WHERE it was to reconstruct the full info if needed,
    # OR we just say "Info" is the full string?
    # The request says: "mostrará el segmento de mensaje".
    # So we want the Name to ID it, and the Full Text to display it.
    
    # Cleanup Name
    nombre_infra = re.sub(r'^(?:(?:Por|El|La|En|del)\s+)+', '', nombre_raw.strip(), flags=re.IGNORECASE)
    nombre_infra = re.sub(r'^Sistema\s+', '', nombre_infra, flags=re.IGNORECASE)
    
    if not nombre_infra or re.match(r'^[,.]', nombre_infra):
        nombre_infra = None
    
    return nombre_infra, nota

def parse_water_distribution(texto_original: str) -> Dict:
    texto = limpiar_texto(texto_original)
    fecha = extraer_fecha(texto)
    
    resultados = []

    # 1. Split by Water Drop 💦 to get Systems
    sistemas_bloques = texto.split('💦')
    
    current_sistema = "General"
    
    for bloque_sys in sistemas_bloques:
        bloque_sys = bloque_sys.strip()
        if not bloque_sys:
            continue
            
        match_sys = re.search(r'Sistema\s+([a-zA-Záéíóúñ ]+)(?::|)', bloque_sys, re.IGNORECASE)
        if match_sys:
            current_sistema = match_sys.group(1).strip()
            bloque_sys = bloque_sys[match_sys.end():]

        # 2. Split by Pointing Finger 👉 to get Notes
        notas = bloque_sys.split('👉')
        
        for nota in notas:
            nota = nota.strip()
            if not nota or len(nota) < 5:
                continue
            
            if "planificación del" in nota.lower():
                continue

            nombre, full_note = extraer_infraestructura(nota)
            
            if nombre:
                resultados.append({
                    "sistema": current_sistema,
                    "infraestructura": nombre,
                    "nota_original": full_note
                })

    return {
        "date": fecha,
        "segments": resultados
    }
