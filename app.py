import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# --- CONEXIÓN DIRECTA A TU HOJA "CATALOGO" ---
# Convertimos tu link en un link de descarga directa de datos
ID_HOJA = "1cRFrckanV-wpOmZjgAuc_o1zJZ-S5K-ZJbgo57t9SBM"
url_csv = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"

# Inicialización de variables
productos_lista = []

@st.cache_data(ttl=10) # Refresca los datos cada 10 segundos
def cargar_datos(url):
    try:
        # Leemos la hoja directamente por internet
        df = pd.read_csv(url)
        # Limpiamos filas vacías
        df = df.dropna(subset=['nombre'])
        return df.to_dict('records')
    except Exception as e:
        return []

productos_lista = cargar_datos(url_csv)

# --- FUNCIÓN PARA IMÁGENES DE DRIVE ---
def convertir_link_directo(url):
    if isinstance(url, str) and "drive.google.com" in url:
        id_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if id_match:
            file_id = id_match.group(1) or id_match.group(2)
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return url

# --- FUNCIÓN FACTURA PDF ---
def crear_factura(cliente, lista_items):
    pdf = FPDF()
    pdf.add_page()
    try: pdf.image('logo.jpg', x=10, y=8, w=30)
    except: pass
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "FACTURA DE VENTA - ZE", ln=True, align='C')
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 10, f"Fecha: {datetime.date.today()}", ln=True)
    pdf.cell(0, 10, f"Cliente: {cliente}", ln=True)
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, " Cod.", border=1, fill=True)
    pdf.cell(110, 10, " Concepto", border=1, fill=True)
    pdf.cell(40, 10, " Precio", border=1, ln=True, fill=True)
    total_final = 0
    pdf.set_font("Arial", size=10)
    for item in lista_items:
        val_precio = float(item.get('precio', 0))
        pdf.cell(30, 10, f" {item.get('id', 'N/A')}", border=1)
        pdf.cell(110, 10, f" {item.get('nombre', 'Item')}", border=1)
        pdf.cell(40, 10, f" ${val_precio}", border=1, ln=True)
        total_final += val_precio
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, " TOTAL A PAGAR", border=0)
    pdf.cell(40, 10, f" ${total_final}", border=0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

col_l, _ = st.columns([1, 4])
with col_l:
    st.image('logo.jpg', width=150)

st.title("Catálogo Digital ZE")

if not productos_lista:
    st.error("⚠️ No se pudieron cargar los productos.")
    st.info("Asegúrate de que en Google Sheets hayas dado clic en 'Compartir' -> 'Cualquier persona con el enlace puede leer'.")
else:
    c_catalogo, c_carrito = st.columns([2, 1])

    with c_catalogo:
        grid = st.columns(2)
        for i, prod in enumerate(productos_lista):
            with grid[i % 2]:
                foto = convertir_link_directo(str(prod.get('img', '')))
                if foto: st.image(foto, use_container_width=True)
                else: st.image("https://via.placeholder.com/150?text=Sin+Foto", use_container_width=True)
                
                st.subheader(prod.get('nombre', 'Producto'))
                st.write(f"Código: {prod.get('id', '000')} | **${prod.get('precio', 0)}**")
                
                if st.button(f"Agregar al pedido", key=f"btn_add_{i}"):
                    st.session_state.carrito.append(prod)
                    st.toast(f"Añadido: {prod['nombre']}")

    with c_carrito:
        st.subheader("🛒 Tu Pedido")
        if st.session_state.carrito:
            suma_total = sum(float(p.get('precio', 0)) for p in st.session_state.carrito)
            for p in st.session_state.carrito:
                st.text(f"• {p['nombre']} (${p['precio']})")
            st.write(f"### Total: ${suma_total}")
            nombre_factura = st.text_input("Nombre del cliente")
            if nombre_factura:
                pdf_out = crear_factura(nombre_factura, st.session_state.carrito)
                st.download_button("📥 Descargar Factura PDF", data=pdf_out, file_name=f"Factura_ZE_{nombre_factura}.pdf")
            if st.button("Vaciar Carrito"):
                st.session_state.carrito = []
                st.rerun()
        else:
            st.info("El pedido está vacío.")
