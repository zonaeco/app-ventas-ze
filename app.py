import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# --- CONEXIÓN A BASE DE DATOS (GOOGLE SHEETS) ---
# REEMPLAZA ESTE LINK POR EL DE TU HOJA REAL
url_hoja = "https://docs.google.com/spreadsheets/d/TU_ID_DE_HOJA/edit?usp=sharing"

# Inicializamos las variables para evitar errores de "NameError"
df = pd.DataFrame()
productos_db = []

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url_hoja)
    productos_db = df.to_dict('records')
except Exception as e:
    st.error("Error de conexión: Verifica que el link de Google Sheets sea público y que la librería esté en requirements.txt")

# --- FUNCIONES ---
def corregir_link_drive(url):
    """Convierte links de Drive en imágenes visibles directamente"""
    if "drive.google.com" in url:
        drive_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if drive_match:
            file_id = drive_match.group(1) or drive_match.group(2)
            # Formato thumbnail: más rápido, ligero y siempre visible
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
        pdf.cell(30, 10, f" {item['id']}", border=1)
        pdf.cell(110, 10, f" {item['nombre']}", border=1)
        pdf.cell(40, 10, f" ${item['precio']}", border=1, ln=True)
        total += item['precio']
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

# --- CABECERA ---
col_logo, _ = st.columns([1, 4])
with col_logo:
    if st.button("🔑", help="Acceso Administrador"):
        st.session_state.admin_mode = not st.session_state.admin_mode
    st.image('logo.jpg', width=150)

# --- PANEL DE ADMINISTRACIÓN ---
if st.session_state.admin_mode:
    st.divider()
    clave = st.text_input("Introduce la clave maestra", type="password")
    if clave == "1234":
        st.success("Acceso concedido al Inventario")
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.info("Para modificar productos, edita tu Google Sheets y refresca esta página.")
        else:
            st.warning("No hay datos para mostrar. Revisa la conexión con la hoja.")
    st.divider()

# --- CATÁLOGO DIGITAL ---
st.title("Catálogo Digital ZE")
col_cat, col_ped = st.columns([2, 1])

with col_cat:
    if productos_db:
        columnas = st.columns(2)
        for i, p in enumerate(productos_db):
            with columnas[i % 2]:
                # Procesar imagen
                img_url = corregir_link_drive(str(p.get('img', '')))
                if img_url:
                    st.image(img_url, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150?text=Sin+Imagen", use_container_width=True)
                
                st.subheader(p.get('nombre', 'Producto sin nombre'))
                st.write(f"Código: {p.get('id', 'N/A')} | **${p.get('precio', 0)}**")
                
                if st.button(
