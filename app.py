import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ZE - Catálogo Digital", layout="wide")

# PEGA AQUÍ TU LINK DE "PUBLICAR EN LA WEB" (el que termina en .csv)
URL_CSV = "https://docs.google.com/spreadsheets/d/1cRFrckanV-wpOmZjgAuc_o1zJZ-S5K-ZJbgo57t9SBM/pub?output=csv"

# --- FUNCIONES DE APOYO ---
@st.cache_data(ttl=5)
def cargar_datos(url):
    try:
        # Lee la hoja publicada directamente
        df = pd.read_csv(url)
        df = df.dropna(subset=['nombre'])
        return df.to_dict('records')
    except:
        return []

def corregir_link_drive(url):
    """Convierte links de Drive en imágenes visibles"""
    if isinstance(url, str) and "drive.google.com" in url:
        drive_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if drive_match:
            file_id = drive_match.group(1) or drive_match.group(2)
            # Formato thumbnail para máxima compatibilidad
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return url

def generar_pdf(nombre_cliente, items):
    pdf = FPDF()
    pdf.add_page()
    try: pdf.image('logo.jpg', x=10, y=8, w=30)
    except: pass
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "FACTURA DE VENTA - ZE", ln=True, align='C')
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 10, f"Fecha: {datetime.date.today()}", ln=True)
    pdf.cell(0, 10, f"Cliente: {nombre_cliente}", ln=True)
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(30, 10, " Cod.", border=1, fill=True)
    pdf.cell(110, 10, " Concepto", border=1, fill=True)
    pdf.cell(40, 10, " Precio", border=1, ln=True, fill=True)
    total = 0
    for item in items:
        precio = float(item.get('precio', 0))
        pdf.cell(30, 10, f" {item.get('id', 'N/A')}", border=1)
        pdf.cell(110, 10, f" {item.get('nombre', 'Item')}", border=1)
        pdf.cell(40, 10, f" ${precio}", border=1, ln=True)
        total += precio
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, " TOTAL A PAGAR", border=0)
    pdf.cell(40, 10, f" ${total}", border=0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA DE LA APP ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Cabecera
col_logo, _ = st.columns([1, 4])
with col_logo:
    st.image('logo.jpg', width=150)

st.title("Catálogo Digital ZE")

productos = cargar_datos(URL_CSV)

if not productos:
    st.warning("⚠️ No se detectan productos. Asegúrate de haber 'Publicado en la web' como CSV.")
else:
    c_cat, c_ped = st.columns([2, 1])

    with c_cat:
        grid = st.columns(2)
        for i, p in enumerate(productos):
            with grid[i % 2]:
                img = corregir_link_drive(str(p.get('img', '')))
                if img: st.image(img, use_container_width=True)
                else: st.image("https://via.placeholder.com/150", use_container_width=True)
                
                st.subheader(p.get('nombre', 'Item'))
                st.write(f"Código: {p.get('id', '---')} | **${p.get('precio', 0)}**")
                if st.button(f"Agregar", key=f"btn_{i}"):
                    st.session_state.carrito.append(p)
                    st.toast(f"Añadido: {p['nombre']}")

    with c_ped:
        st.subheader("🛒 Pedido")
        if st.session_state.carrito:
            total_v = sum(float(x.get('precio', 0)) for x in st.session_state.carrito)
            for x in st.session_state.carrito:
                st.text(f"• {x['nombre']} (${x['precio']})")
            st.write(f"### Total: ${total_v}")
            
            cliente = st.text_input("Nombre del cliente")
            if cliente:
                factura = generar_pdf(cliente, st.session_state.carrito)
                st.download_button("📥 Descargar Factura PDF", data=factura, file_name=f"ZE_{cliente}.pdf")
            
            if st.button("Vaciar Carrito"):
                st.session_state.carrito = []
                st.rerun()
        else:
            st.info("El carrito está vacío")
