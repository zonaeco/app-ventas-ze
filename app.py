import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# --- CONEXIÓN A TU HOJA DE CÁLCULO REAL ---
url_hoja = "https://docs.google.com/spreadsheets/d/1cRFrckanV-wpOmZjgAuc_o1zJZ-S5K-ZJbgo57t9SBM/edit?usp=sharing"

# Inicializamos variables de seguridad para evitar errores rojos
df_actual = pd.DataFrame()
productos_db = []

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Leemos la hoja (esto fallará si no has puesto los títulos en la fila 1)
    df_actual = conn.read(spreadsheet=url_hoja)
    productos_db = df_actual.to_dict('records')
except Exception as e:
    st.error("⚠️ Error de conexión: Revisa que tu hoja tenga los títulos id, nombre, precio, img en la fila 1.")
    productos_db = [{"id": "ERR", "nombre": "Error de Conexión", "precio": 0, "img": ""}]

# --- FUNCIÓN PARA IMÁGENES DE DRIVE ---
def corregir_link_drive(url):
    if isinstance(url, str) and "drive.google.com" in url:
        drive_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if drive_match:
            file_id = drive_match.group(1) or drive_match.group(2)
            # Formato thumbnail para que la foto se vea siempre
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return url

# --- FUNCIÓN PARA FACTURA PDF ---
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

# --- INTERFAZ ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

col_logo, _ = st.columns([1, 4])
with col_logo:
    st.image('logo.jpg', width=150)

st.title("Catálogo Digital ZE")
c1, c2 = st.columns([2, 1])

with c1:
    if productos_db:
        cols = st.columns(2)
        for i, row in enumerate(productos_db):
            with cols[i % 2]:
                img_url = corregir_link_drive(str(row.get('img', '')))
                if img_url:
                    st.image(img_url, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150?text=Sin+Foto", use_container_width=True)
                st.subheader(row.get('nombre', 'Producto'))
                st.write(f"Cod: {row.get('id', '000')} | **${row.get('precio', 0)}**")
                if st.button(f"Añadir", key=f"add_{i}"):
                    st.session_state.carrito.append(row)
                    st.toast("Agregado")

with c2:
    st.subheader("🛒 Tu Pedido")
    if st.session_state.carrito:
        total_p = sum(float(item.get('precio', 0)) for item in st.session_state.carrito)
        for item in st.session_state.carrito:
            st.text(f"• {item.get('nombre')} (${item.get('precio')})")
        st.write(f"### Total: ${total_p}")
        nom_c = st.text_input("Nombre del cliente")
        if nom_c:
            pdf_data = generar_pdf(nom_c, st.session_state.carrito)
            st.download_button("📥 Descargar Factura", data=pdf_data, file_name=f"ZE_{nom_c}.pdf")
        if st.button("Vaciar"):
            st.session_state.carrito = []
            st.rerun()
