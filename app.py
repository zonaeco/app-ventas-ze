import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZE - Catálogo Digital", layout="wide")

# URL de tu hoja (Publicada como CSV)
# Asegúrate de que este link termine exactamente en pub?output=csv
URL_DATOS = "https://docs.google.com/spreadsheets/d/1cRFrckanV-wpOmZjgAuc_o1zJZ-S5K-ZJbgo57t9SBM/pub?output=csv"

# --- FUNCIONES DE APOYO ---
@st.cache_data(ttl=5)
def cargar_inventario(url):
    try:
        # Intenta cargar desde el link publicado
        df = pd.read_csv(url)
        # Limpia filas vacías y asegura que los encabezados existan
        df.columns = [c.lower().strip() for c in df.columns]
        df = df.dropna(subset=['nombre'])
        return df.to_dict('records')
    except Exception as e:
        # Si falla, devuelve una lista vacía para manejar el error con gracia
        return []

def corregir_link_drive(url):
    """Convierte links de Drive en imágenes visibles"""
    if isinstance(url, str) and "drive.google.com" in url:
        drive_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if drive_match:
            file_id = drive_match.group(1) or drive_match.group(2)
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
        p_precio = float(item.get('precio', 0))
        pdf.cell(30, 10, f" {item.get('id', 'N/A')}", border=1)
        pdf.cell(110, 10, f" {item.get('nombre', 'Item')}", border=1)
        pdf.cell(40, 10, f" ${p_precio}", border=1, ln=True)
        total += p_precio
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, " TOTAL A PAGAR", border=0)
    pdf.cell(40, 10, f" ${total}", border=0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA PRINCIPAL ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Cabecera
col_logo, _ = st.columns([1, 4])
with col_logo:
    st.image('logo.jpg', width=150)

st.title("Catálogo Digital ZE")

# Intento de carga
productos = cargar_inventario(URL_DATOS)

# Si la carga automática falla, mostramos una advertencia pero permitimos seguir
if not productos:
    st.error("⚠️ La App no pudo leer los datos automáticamente de Google Sheets.")
    st.info("Esto sucede si el link de 'Publicar en la web' no se ha actualizado. Intenta refrescar la página en 1 minuto.")
    # Datos de respaldo para que la App no esté vacía
    productos = [{"id": "001", "nombre": "Giron Exclusivo (Modo Local)", "precio": 4500, "img": ""}]

# Mostrar Catálogo
c_cat, c_ped = st.columns([2, 1])

with c_cat:
    grid = st.columns(2)
    for i, p in enumerate(productos):
        with grid[i % 2]:
            img_url = corregir_link_drive(str(p.get('img', '')))
            if img_url: st.image(img_url, use_container_width=True)
            else: st.image("https://via.placeholder.com/150", use_container_width=True)
            
            st.subheader(p.get('nombre', 'Producto'))
            st.write(f"Cod: {p.get('id', '---')} | **${p.get('precio', 0)}**")
            
            if st.button(f"Añadir", key=f"btn_{i}"):
                st.session_state.carrito.append(p)
                st.toast(f"Agregado: {p['nombre']}")

with c_ped:
    st.subheader("🛒 Tu Pedido")
    if st.session_state.carrito:
        total_venta = sum(float(x.get('precio', 0)) for x in st.session_state.carrito)
        for x in st.session_state.carrito:
            st.text(f"• {x['nombre']} (${x['precio']})")
        st.write(f"### Total: ${total_venta}")
        
        nombre_c = st.text_input("Nombre del cliente")
        if nombre_c:
            pdf_data = generar_pdf(nombre_c, st.session_state.carrito)
            st.download_button("📥 Descargar Factura PDF", data=pdf_data, file_name=f"Factura_{nombre_c}.pdf")
        
        if st.button("Vaciar Carrito"):
            st.session_state.carrito = []
            st.rerun()
    else:
        st.info("Carrito vacío")
