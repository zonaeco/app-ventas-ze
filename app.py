import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# --- CONEXIÓN A TU HOJA DE CÁLCULO REAL ---
# He actualizado el link con el ID de tu hoja "Catalogo"
url_hoja = "https://docs.google.com/spreadsheets/d/1cRFrckanV-wpOmZjgAuc_o1zJZ-S5K-ZJbgo57t9SBM/edit?usp=sharing"

# Inicializamos variables para evitar errores visuales
df_actual = pd.DataFrame()
productos_db = []

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Leemos la hoja con tus datos reales
    df_actual = conn.read(spreadsheet=url_hoja, ttl=5) # ttl=5 para que refresque rápido
    productos_db = df_actual.to_dict('records')
except Exception as e:
    st.error("⚠️ Error de conexión con Google Sheets. Revisa los permisos de la hoja.")
    # Datos de respaldo por si falla la red
    productos_db = [{"id": "001", "nombre": "Cargando...", "precio": 0, "img": ""}]

# --- FUNCIÓN PARA IMÁGENES DE DRIVE ---
def corregir_link_drive(url):
    """Transforma links de Drive en imágenes visibles directamente"""
    if isinstance(url, str) and "drive.google.com" in url:
        drive_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if drive_match:
            file_id = drive_match.group(1) or drive_match.group(2)
            # Usamos formato thumbnail para que la foto aparezca en el catálogo
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return url

# --- FUNCIÓN PARA FACTURA PDF ---
def generar_pdf(nombre_cliente, items):
    pdf = FPDF()
    pdf.add_page()
    try: 
        pdf.image('logo.jpg', x=10, y=8, w=30) # Usa el logo que ya tienes en GitHub
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
        cols_cat = st.columns(2)
        for i, row in enumerate(productos_db):
            with cols_cat[i % 2]:
                # Mostramos la FOTO del producto
                url_img = corregir_link_drive(str(row.get('img', '')))
                if url_img:
                    st.image(url_img, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150?text=Sin+Foto", use_container_width=True)
                
                st.subheader(row.get('nombre', 'Producto'))
                st.write(f"Código: {row.get('id', '000')} | **${row.get('precio', 0)}**")
                
                if st.button(f"Añadir al pedido", key=f"btn_{i}"):
                    st.session_state.carrito.append(row)
                    st.toast(f"Agregado: {row['nombre']}")
    else:
        st.info("Cargando productos desde la hoja...")

with c2:
    st.subheader("🛒 Tu Pedido")
    if st.session_state.carrito:
        total_venta = sum(float(item.get('precio', 0)) for item in st.session_state.carrito)
        for item in st.session_state.carrito:
            st.text(f"• {item.get('nombre')} (${item.get('precio')})")
        
        st.write(f"### Total: ${total_venta}")
        nombre_cli = st.text_input("Nombre del cliente")
        
        if nombre_cli:
            pdf_bytes = generar_pdf(nombre_cli, st.session_state.carrito)
            st.download_button("📥 Descargar Factura PDF", data=pdf_bytes, file_name=f"ZE_{nombre_cli}.pdf")
            
        if st.button("Vaciar Pedido"):
            st.session_state.carrito = []
            st.rerun()
    else:
        st.info("El pedido está vacío")
