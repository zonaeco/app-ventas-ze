import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# --- CONEXIÓN A BASE DE DATOS ---
# IMPORTANTE: Cambia este link por el tuyo y asegúrate que sea público
url_hoja = "https://docs.google.com/spreadsheets/d/URL_DE_TU_HOJA/edit?usp=sharing"

# Inicializamos variables de seguridad
df = pd.DataFrame()
productos_db = []

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url_hoja)
    # Convertimos los datos de la hoja a una lista de productos
    productos_db = df.to_dict('records')
except Exception as e:
    # Si falla el Google Sheets, cargamos productos de respaldo para que la app funcione
    productos_db = [
        {"id": "001", "nombre": "Imán Girón (Ejemplo)", "precio": 15000, "img": ""},
        {"id": "002", "nombre": "Corte Láser (Ejemplo)", "precio": 45000, "img": ""}
    ]
    st.warning("Usando inventario local. Revisa la conexión con Google Sheets.")

# --- FUNCIONES ---
def corregir_link_drive(url):
    """Transforma links de Drive en imágenes visibles"""
    if isinstance(url, str) and "drive.google.com" in url:
        drive_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if drive_match:
            file_id = drive_match.group(1) or drive_match.group(2)
            # El formato 'thumbnail' es el más compatible para mostrar la foto
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
        p_nombre = item.get('nombre', 'Item')
        p_id = item.get('id', 'N/A')
        p_precio = item.get('precio', 0)
        pdf.cell(30, 10, f" {p_id}", border=1)
        pdf.cell(110, 10, f" {p_nombre}", border=1)
        pdf.cell(40, 10, f" ${p_precio}", border=1, ln=True)
        total += float(p_precio)
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
    if st.button("🔑"):
        st.session_state.admin_mode = not st.session_state.admin_mode
    st.image('logo.jpg', width=150)

# Panel de Administración
if st.session_state.admin_mode:
    clave = st.text_input("Clave maestra", type="password")
    if clave == "1234":
        st.success("Conexión establecida")
        st.dataframe(df, use_container_width=True)
    st.divider()

# --- CUERPO DE LA APP ---
st.title("Catálogo Digital ZE")
c1, c2 = st.columns([2, 1])

with c1:
    if productos_db:
        cols = st.columns(2)
        for i, p in enumerate(productos_db):
            with cols[i % 2]:
                # Mostramos la imagen
                url_limpia = corregir_link_drive(p.get('img', ''))
                if url_limpia:
                    st.image(url_limpia, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150?text=Sin+Foto", use_container_width=True)
                
                st.subheader(p.get('nombre', 'Producto'))
                st.write(f"Código: {p.get('id', '000')} | **${p.get('precio', 0)}**")
                
                if st.button(f"Añadir al pedido", key=f"btn_{i}"):
                    st.session_state.carrito.append(p)
                    st.toast(f"Agregado: {p['nombre']}")
    else:
        st.error("No se encontraron productos.")

with c2:
    st.subheader("🛒 Tu Selección")
    if st.session_state.carrito:
        total_acumulado = 0
        for item in st.session_state.carrito:
            st.text(f"• {item['nombre']} (${item['precio']})")
            total_acumulado += float(item['precio'])
        
        st.write(f"### Total: ${total_acumulado}")
        nombre_cli = st.text_input("Nombre del cliente")
        
        if nombre_cli:
            pdf_bytes = generar_pdf(nombre_cli, st.session_state.carrito)
            st.download_button("📥 Descargar Factura PDF", data=pdf_bytes, file_name=f"Factura_{nombre_cli}.pdf")
            
        if st.button("Vaciar Carrito"):
            st.session_state.carrito = []
            st.rerun()
    else:
        st.info("El carrito está vacío.")
