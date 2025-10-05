import requests
import pdfplumber
import io
import json
from datetime import datetime
import os

# === CONFIGURACIÓN ===
PDF_URL = "https://ctagr.es/wp-content/uploads/horarios/20250916/L111L.pdf"
NOMBRE_LINEA = "L-111"
PHP_ENDPOINT = os.getenv("PHP_ENDPOINT")

# === ETAPA 1: Extraer tablas del PDF ===
def extraer_tablas(pdf_url):
    response = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        print("Error al descargar el PDF:", response.status_code)
        return None
    pdf_data = io.BytesIO(response.content)
    tablas = []
    with pdfplumber.open(pdf_data) as pdf:
        for pagina in pdf.pages:
            for tabla in pagina.extract_tables():
                tablas.append(tabla)
    return tablas

# === ETAPA 2: Limpiar y estructurar datos ===
def limpiar_tabla(tabla):
    if not tabla or len(tabla) < 2:
        return []
    cabeceras = [c for c in tabla[0] if c and c.strip()]
    horarios = []
    for fila in tabla[1:]:
        horas = [h for h in fila if h and h.strip()]
        if len(horas) == len(cabeceras):
            horarios.append(dict(zip(cabeceras, horas)))
    return horarios

# === ETAPA 3: Procesar PDF completo ===
def procesar_pdf(pdf_url, nombre_linea):
    tablas = extraer_tablas(pdf_url)
    if not tablas:
        return None
    resultado = {
        "linea": nombre_linea,
        "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sentidos": []
    }
    for i, tabla in enumerate(tablas, start=1):
        horarios_limpios = limpiar_tabla(tabla)
        if horarios_limpios:
            resultado["sentidos"].append({
                "tabla": i,
                "horarios": horarios_limpios
            })
    return resultado

# === ETAPA 4: Enviar datos al servidor ===
def enviar_a_bd(nombre_linea, datos_json):
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "nombre_linea": nombre_linea,
        "fecha": fecha_actual,
        "datos": json.dumps(datos_json, ensure_ascii=False)
    }

    try:
        r = requests.post(PHP_ENDPOINT, data=payload, timeout=10)
        if r.status_code == 200:
            print("✅ Datos enviados correctamente al servidor.")
            print("Respuesta del servidor:", r.text)
        else:
            print("⚠️ Error al enviar datos. Código:", r.status_code)
    except Exception as e:
        print("❌ Error de conexión:", e)

# === MAIN ===
if __name__ == "__main__":
    datos = procesar_pdf(PDF_URL, NOMBRE_LINEA)
    if datos:
        print("PDF procesado correctamente. Enviando datos al servidor...")
        enviar_a_bd(NOMBRE_LINEA, datos)
    else:
        print("No se pudieron extraer datos del PDF.")

