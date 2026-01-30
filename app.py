import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ZE - Catálogo Digital", layout="wide")

# TU LINK DE PUBLICACIÓN (Asegúrate que termine en pub?output=csv)
URL_CSV = "https://docs.google.com/spreadsheets/d/1cRFrckanV-wpOmZjgAuc_o1zJZ-S5K-ZJbgo57t9SBM/pub?output=csv"

# --- FUNCIONES ---
def corregir_link_drive(url):
    """Convierte links de Drive en fotos visibles"""
    if isinstance(url, str) and "drive.google.com" in url:
        drive_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if drive_match:
            file_id = drive_match.group(1) or drive_match.group(2)
            # Este formato es el que permite ver la FOTO directamente
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return url

@st.cache_data(ttl=2) # <--- ESTO HACE QUE SE ACTUALICE CADA 2 SEGUNDOS
def cargar_inventario(url):
    try:
        # Forzamos la descarga de los datos frescos
        df = pd.read_csv(url)
        df.columns = [c.lower().strip() for c in df.columns]
        return df.to_dict('records')
    except:
        # Datos de rescate si la red falla
        return [{"id": "001", "nombre": "Girón Exclusivo", "precio": 4500, "img": "https://drive.google.com/file/d/1HKsPLzxChe7cwiewRCGHf5wH-u_xrvt_/view"}]

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

# Botón para forzar actualización manual
if st.button("🔄 Actualizar Catálogo"):
    st.cache_data.clear()
    st.rerun()

productos = cargar_inventario(URL_CSV)

c_cat, c_ped = st.columns([2, 1])

with c_cat:
    grid = st.columns(2)
    for i, p in enumerate(productos):
        with grid[i % 2]:
            foto = corregir_link_drive(str(p.get('img', '')))
            if foto: st.image(foto, use_container_width=True)
            else: st.image("https://via.placeholder.com/150", use_container_width=True)
            
            st.subheader(p.get('nombre', 'Producto'))
            st.write(f"Cod: {p.get('id', '---')} | **${p.get('precio', 0)}**")
            
            if st.button(f"Seleccionar", key=f"btn_{i}"):
                st.session_state.carrito.append(p)
                st.toast(f"Agregado: {p['nombre']}")

with c_ped:
    st.subheader("🛒 Tu Pedido")
    if st.session_state.carrito:
        total_p = sum(float(x.get('precio', 0)) for x in st.session_state.carrito)
        for x in st.session_state.carrito:
            st.text(f"• {x['nombre']} (${x['precio']})")
        st.write(f"### Total: ${total_p}")
        
        nombre_c = st.text_input("Nombre del cliente")
        if nombre_c:
            pdf_data = generar_pdf(nombre_c, st.session_state.carrito)
            st.download_button("📥 Descargar Factura", data=pdf_data, file_name=f"ZE_{nombre_c}.pdf")
        
        if st.button("Vaciar Carrito"):
            st.session_state.carrito = []
            st.rerun()
    else:
        st.info("Selecciona productos para tu pedido.")
