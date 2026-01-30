import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# --- CONEXIÓN A BASE DE DATOS (GOOGLE SHEETS) ---
# REEMPLAZA ESTE LINK POR EL DE TU HOJA REAL (asegúrate que sea público)
url_hoja = "https://docs.google.com/spreadsheets/d/TU_ID_DE_HOJA/edit?usp=sharing"

# Inicializamos variables para evitar NameError
df = pd.DataFrame()
productos_db = []

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url_hoja)
    productos_db = df.to_dict('records')
except Exception as e:
    st.error("Error de conexión con Google Sheets. Verifica el link y permisos.")

# --- FUNCIONES ---
def corregir_link_drive(url):
    """Convierte links de Drive en fotos visibles"""
    if isinstance(url, str) and "drive.google.com" in url:
        drive_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if drive_match:
            file_id = drive_match.group(1) or drive_match.group(2)
            # Formato thumbnail para que la imagen se vea en el catálogo
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return url

def generar_pdf(nombre_cliente, items):
    pdf = FPDF()
    pdf.add_page()
    try: 
        pdf.image('logo.jpg', x=10, y=8, w=30)
    except: 
        pass
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
        pdf.cell(30, 10, f" {item.get('id', 'N/A')}", border=1)
        pdf.cell(110, 10, f" {item.get('nombre', 'Item')}", border=1)
        pdf.cell(40, 10, f" ${item.get('precio', 0)}", border=1, ln=True)
        total += float(item.get('precio', 0))
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, " TOTAL A PAGAR", border=0)
    pdf.cell(40, 10, f" ${total}", border=0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- ESTADOS DE SESIÓN ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False

# --- INTERFAZ ---
col_logo, _ = st.columns([1, 4])
with col_logo:
    if st.button("🔑", help="Administrador"):
        st.session_state.admin_mode = not st.session_state.admin_mode
    st.image('logo.jpg', width=150)

# Panel Admin
if st.session_state.admin_mode:
    st.divider()
    clave = st.text_input("Clave maestra", type="password")
    if clave == "1234":
        st.success("Acceso concedido")
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No hay datos en la hoja.")
    st.divider()

# Catálogo
st.title("Catálogo Digital ZE")
c1, c2 = st.columns([2, 1])

with c1:
    if productos_db:
        columnas = st.columns(2)
        for i, p in enumerate(productos_db):
            with columnas[i % 2]:
                img_url = corregir_link_drive(p.get('img', ''))
                if img_url:
                    st.image(img_url, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150", use_container_width=True)
                
                st.subheader(p.get('nombre', 'Producto'))
                st.write(f"Cod: {p.get('id', '000')} | **${p.get('precio', 0)}**")
                
                if st.button(f"Añadir", key=f"add_{i}"):
                    st.session_state.carrito.append(p)
                    st.toast(f"Añadido: {p['nombre']}")
    else:
        st.info("Cargando catálogo...")

with c2:
    st.subheader("🛒 Tu Pedido")
    if st.session_state.carrito:
        total_p = 0
        for item in st.session_state.carrito:
            st.text(f"• {item['nombre']} (${item['precio']})")
            total_p += float(item['precio'])
        st.write(f"### Total: ${total_p}")
        
        nombre_c = st.text_input("Nombre del cliente")
        if nombre_c:
            pdf_data = generar_pdf(nombre_c, st.session_state.carrito)
            st.download_button("📥 Descargar Factura PDF", data=pdf_data, file_name=f"ZE_{nombre_c}.pdf")
        
        if st.button("Vaciar carrito"):
            st.session_state.carrito = []
            st.rerun()
    else:
        st.info("El carrito está vacío")
