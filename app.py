import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# --- CONEXIÓN DIRECTA Y SEGURA A TU HOJA ---
# Este enlace descarga los datos directamente sin pasar por validaciones complejas
ID_HOJA = "1cRFrckanV-wpOmZjgAuc_o1zJZ-S5K-ZJbgo57t9SBM"
URL_DATOS = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/export?format=csv"

# Función optimizada para cargar datos
@st.cache_data(ttl=5) # Refresca cada 5 segundos para que veas tus cambios rápido
def obtener_inventario(url):
    try:
        # Leemos la hoja como un archivo de datos puro
        df = pd.read_csv(url)
        # Limpiamos filas que no tengan nombre para evitar errores
        df = df.dropna(subset=['nombre'])
        return df.to_dict('records')
    except Exception as e:
        return []

# Intentamos cargar tus productos reales
productos_lista = obtener_inventario(URL_DATOS)

# --- FUNCIÓN PARA IMÁGENES DE DRIVE ---
def formatear_link_foto(url):
    if isinstance(url, str) and "drive.google.com" in url:
        # Extraemos el código de la imagen para que Streamlit la pueda dibujar
        id_foto = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if id_foto:
            file_id = id_foto.group(1) or id_foto.group(2)
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return url

# --- FUNCIÓN FACTURA PDF ---
def crear_pdf(nombre_cliente, items_seleccionados):
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
    
    # Tabla
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, " Cod.", border=1, fill=True)
    pdf.cell(110, 10, " Concepto", border=1, fill=True)
    pdf.cell(40, 10, " Precio", border=1, ln=True, fill=True)
    
    total = 0
    pdf.set_font("Arial", size=10)
    for p in items_seleccionados:
        precio_num = float(p.get('precio', 0))
        pdf.cell(30, 10, f" {p.get('id', 'N/A')}", border=1)
        pdf.cell(110, 10, f" {p.get('nombre', 'Item')}", border=1)
        pdf.cell(40, 10, f" ${precio_num}", border=1, ln=True)
        total += precio_num
        
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, " TOTAL A PAGAR", border=0)
    pdf.cell(40, 10, f" ${total}", border=0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# Logo
col_logo, _ = st.columns([1, 4])
with col_logo:
    st.image('logo.jpg', width=150)

st.title("Catálogo Digital ZE")

if not productos_lista:
    st.error("⚠️ No pudimos conectar con tu Google Sheets.")
    st.info("Asegúrate de que en tu hoja 'Catalogo' los títulos de la primera fila sean exactamente: id, nombre, precio, img")
else:
    c_izq, c_der = st.columns([2, 1])

    with c_izq:
        grid = st.columns(2)
        for i, item in enumerate(productos_lista):
            with grid[i % 2]:
                # Mostramos la foto real
                foto_url = formatear_link_foto(str(item.get('img', '')))
                if foto_url:
                    st.image(foto_url, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/150", use_container_width=True)
                
                st.subheader(item.get('nombre', 'Item'))
                st.write(f"Cod: {item.get('id', '---')} | **${item.get('precio', 0)}**")
                
                if st.button(f"Agregar al pedido", key=f"btn_{i}"):
                    st.session_state.carrito.append(item)
                    st.toast(f"Añadido: {item['nombre']}")

    with c_der:
        st.subheader("🛒 Tu Pedido")
        if st.session_state.carrito:
            total_pedido = sum(float(x.get('precio', 0)) for x in st.session_state.carrito)
            for x in st.session_state.carrito:
                st.text(f"• {x['nombre']} (${x['precio']})")
            
            st.write(f"### Total: ${total_pedido}")
            
            nombre_cliente = st.text_input("Nombre para la factura")
            if nombre_cliente:
                pdf_factura = crear_pdf(nombre_cliente, st.session_state.carrito)
                st.download_button(
                    label="📥 Descargar Factura PDF",
                    data=pdf_factura,
                    file_name=f"Factura_{nombre_cliente}.pdf",
                    mime="application/pdf"
                )
            
            if st.button("Vaciar Carrito"):
                st.session_state.carrito = []
                st.rerun()
        else:
            st.info("Selecciona productos del catálogo")
