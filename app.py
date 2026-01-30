import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="ZE - Catálogo Digital", layout="wide")

# --- ENLACE DE DATOS ---
# REEMPLAZA ESTE LINK POR EL QUE OBTUVISTE AL "PUBLICAR EN LA WEB" COMO CSV
URL_CSV = "https://docs.google.com/spreadsheets/d/1cRFrckanV-wpOmZjgAuc_o1zJZ-S5K-ZJbgo57t9SBM/pub?output=csv"

# --- FUNCIONES ---
@st.cache_data(ttl=5)
def cargar_inventario(url):
    try:
        # Cargamos los datos directamente desde el enlace público
        df = pd.read_csv(url)
        # Limpiamos filas sin nombre
        df = df.dropna(subset=['nombre'])
        return df.to_dict('records')
    except Exception as e:
        return []

def corregir_link_drive(url):
    """Convierte links de Drive en fotos que se pueden ver en la App"""
    if isinstance(url, str) and "drive.google.com" in url:
        id_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if id_match:
            file_id = id_match.group(1) or id_match.group(2)
            # Usamos el formato thumbnail para que cargue rápido
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return url

def generar_factura_pdf(nombre_cliente, productos_carrito):
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
    
    # Tabla de productos
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, " Cod.", border=1, fill=True)
    pdf.cell(110, 10, " Concepto", border=1, fill=True)
    pdf.cell(40, 10, " Precio", border=1, ln=True, fill=True)
    
    total_pagar = 0
    pdf.set_font("Arial", size=10)
    for item in productos_carrito:
        precio_item = float(item.get('precio', 0))
        pdf.cell(30, 10, f" {item.get('id', 'N/A')}", border=1)
        pdf.cell(110, 10, f" {item.get('nombre', 'Item')}", border=1)
        pdf.cell(40, 10, f" ${precio_item}", border=1, ln=True)
        total_pagar += precio_item
        
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, " TOTAL", border=0)
    pdf.cell(40, 10, f" ${total_pagar}", border=0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA DE LA APLICACIÓN ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Mostrar Logo
col_l, _ = st.columns([1, 4])
with col_l:
    st.image('logo.jpg', width=150)

st.title("Catálogo Digital ZE")

# Cargar los productos desde Google Sheets
inventario = cargar_inventario(URL_CSV)

if not inventario:
    st.error("⚠️ No se pudieron cargar los datos.")
    st.info("Asegúrate de haber 'Publicado en la web' como CSV en Google Sheets.")
else:
    c_cat, c_car = st.columns([2, 1])

    with c_cat:
        # Mostrar productos en 2 columnas
        grid = st.columns(2)
        for i, prod in enumerate(inventario):
            with grid[i % 2]:
                # Procesar y mostrar la imagen
                link_foto = corregir_link_drive(str(prod.get('img', '')))
                if link_foto:
                    st.image(link_foto, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150", use_container_width=True)
                
                st.subheader(prod.get('nombre', 'Producto'))
                st.write(f"Código: {prod.get('id', '---')} | **${prod.get('precio', 0)}**")
                
                if st.button(f"Añadir al carrito", key=f"btn_{i}"):
                    st.session_state.carrito.append(prod)
                    st.toast(f"Agregado: {prod['nombre']}")

    with c_car:
        st.subheader("🛒 Pedido Actual")
        if st.session_state.carrito:
            total_pedido = 0
            for p in st.session_state.carrito:
                st.text(f"• {p['nombre']} (${p['precio']})")
                total_pedido += float(p['precio'])
            
            st.write(f"### Total: ${total_pedido}")
            
            nombre_fact = st.text_input("Nombre del cliente")
            if nombre_fact:
                pdf_fact = generar_factura_pdf(nombre_fact, st.session_state.carrito)
                st.download_button("📥 Descargar Factura PDF", data=pdf_fact, file_name=f"ZE_{nombre_fact}.pdf")
            
            if st.button("Vaciar Carrito"):
                st.session_state.carrito = []
                st.rerun()
        else:
            st.info("Selecciona productos del catálogo para comenzar.")
