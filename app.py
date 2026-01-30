import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# --- CONEXIÓN A TU HOJA "CATALOGO" ---
# Link verificado de tu captura de pantalla
url_hoja = "https://docs.google.com/spreadsheets/d/1cRFrckanV-wpOmZjgAuc_o1zJZ-S5K-ZJbgo57t9SBM/edit?usp=sharing"

# Inicialización de variables para evitar errores visuales
df_productos = pd.DataFrame()
productos_lista = []

try:
    # Creamos la conexión
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Intentamos leer la "Hoja 1" que es la que tienes en tu captura
    # ttl=0 obliga a la app a buscar datos frescos siempre
    df_productos = conn.read(spreadsheet=url_hoja, worksheet="Hoja 1", ttl=0)
    
    # Limpiamos datos: eliminamos filas que no tengan nombre para evitar errores
    df_productos = df_productos.dropna(subset=['nombre'])
    productos_lista = df_productos.to_dict('records')
except Exception as e:
    st.error("⚠️ La aplicación no pudo leer tu Google Sheets.")
    st.info("Revisa que en el botón 'Compartir' de la hoja diga: 'Cualquier persona con el enlace puede leer'.")
    # Datos de emergencia para que la página no salga en blanco
    productos_lista = [{"id": "---", "nombre": "Esperando conexión...", "precio": 0, "img": ""}]

# --- FUNCIÓN PARA IMÁGENES DE DRIVE ---
def convertir_link_directo(url):
    """Transforma el link de compartir en una imagen visible"""
    if isinstance(url, str) and "drive.google.com" in url:
        id_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if id_match:
            file_id = id_match.group(1) or id_match.group(2)
            # Formato thumbnail: es el más estable para Streamlit
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return url

# --- FUNCIÓN FACTURA PDF ---
def crear_factura(cliente, lista_items):
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
    pdf.cell(0, 10, f"Cliente: {cliente}", ln=True)
    pdf.ln(10)
    
    # Encabezados de tabla
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

# --- INTERFAZ DE USUARIO ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Cabecera con Logo
col_l, _ = st.columns([1, 4])
with col_l:
    st.image('logo.jpg', width=150)

st.title("Catálogo Digital ZE")
st.write("Selecciona tus productos para generar la factura.")

c_catalogo, c_carrito = st.columns([2, 1])

with c_catalogo:
    if productos_lista:
        grid = st.columns(2)
        for i, prod in enumerate(productos_lista):
            with grid[i % 2]:
                # Procesar imagen de Drive
                foto = convertir_link_directo(str(prod.get('img', '')))
                if foto:
                    st.image(foto, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150?text=Sin+Foto", use_container_width=True)
                
                st.subheader(prod.get('nombre', 'Cargando...'))
                st.write(f"Código: {prod.get('id', '000')} | **${prod.get('precio', 0)}**")
                
                if st.button(f"Agregar al pedido", key=f"btn_add_{i}"):
                    st.session_state.carrito.append(prod)
                    st.toast(f"Añadido: {prod['nombre']}")
    else:
        st.info("Buscando productos en tu hoja 'Catalogo'...")

with c_carrito:
    st.subheader("🛒 Tu Pedido")
    if st.session_state.carrito:
        suma_total = 0
        for p in st.session_state.carrito:
            st.text(f"• {p['nombre']} (${p['precio']})")
            suma_total += float(p['precio'])
        
        st.write(f"### Total: ${suma_total}")
        
        nombre_factura = st.text_input("Nombre del cliente")
        if nombre_factura:
            pdf_out = crear_factura(nombre_factura, st.session_state.carrito)
            st.download_button(
                label="📥 Descargar Factura PDF",
                data=pdf_out,
                file_name=f"Factura_ZE_{nombre_factura}.pdf",
                mime="application/pdf"
            )
            
        if st.button("Vaciar Carrito"):
            st.session_state.carrito = []
            st.rerun()
    else:
        st.info("El pedido está vacío.")
