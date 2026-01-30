import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# SUSTITUYE ESTA URL POR LA DE TU HOJA DE CALCULO REAL
url_hoja = "https://docs.google.com/spreadsheets/d/TU_ID_DE_HOJA/edit?usp=sharing"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url_hoja)
    productos_db = df.to_dict('records')
except:
    # Si la hoja no carga, usa productos de respaldo para que la app no se rompa
    productos_db = [{"id": "001", "nombre": "Imán Prueba", "precio": 1000, "img": ""}]

# --- FUNCIONES ---
def corregir_link_drive(url):
    if "drive.google.com" in url:
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
        pdf.cell(30, 10, f" {item['id']}", border=1)
        pdf.cell(110, 10, f" {item['nombre']}", border=1)
        pdf.cell(40, 10, f" ${item['precio']}", border=1, ln=True)
        total += item['precio']
    pdf.ln(5)
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
    if st.button("🔑"):
        st.session_state.admin_mode = not st.session_state.admin_mode
    st.image('logo.jpg', width=150)

# Panel Admin (Solo visualización en esta etapa)
if st.session_state.admin_mode:
    pw = st.text_input("Clave", type="password")
    if pw == "1234":
        st.write("### Inventario en Google Sheets")
        st.dataframe(df)
        st.info("Para modificar, edita directamente tu hoja de Google Sheets y refresca esta página.")

# Catálogo
st.title("Catálogo Digital ZE")
c1, c2 = st.columns([2, 1])

with c1:
    columnas = st.columns(2)
    for i, p in enumerate(productos_db):
        with columnas[i % 2]:
            img_url = corregir_link_drive(str(p['img']))
            st.image(img_url if img_url else "https://via.placeholder.com/150", use_container_width=True)
            st.subheader(p['nombre'])
            st.write(f"Código: {p['id']} | **${p['precio']}**")
            if st.button(f"Agregar", key=f"add_{i}"):
                st.session_state.carrito.append(p)
                st.toast("Añadido")

with c2:
    st.subheader("🛒 Tu Pedido")
    if st.session_state.carrito:
        total_v = sum(item['precio'] for item in st.session_state.carrito)
        for item in st.session_state.carrito:
            st.text(f"• {item['nombre']} (${item['precio']})")
        st.write(f"### Total: ${total_v}")
        nom = st.text_input("Nombre del cliente")
        if nom:
            pdf = generar_pdf(nom, st.session_state.carrito)
            st.download_button("Descargar Factura", data=pdf, file_name=f"ZE_{nom}.pdf")
    else:
        st.info("Vacío")
