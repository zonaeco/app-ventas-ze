import streamlit as st
from fpdf import FPDF
import datetime

# --- CONFIGURACIÓN VISUAL PROFESIONAL ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# Estilo CSS para colores leves y profesionales
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #ffffff;
        color: #333;
        border: 1px solid #ddd;
        border-radius: 5px;
    }
    .stButton>button:hover {
        border-color: #000;
        background-color: #f0f0f0;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO EN LA PÁGINA ---
# Esto muestra tu logo al principio de la web
col_logo, _ = st.columns([1, 4])
with col_logo:
    st.image('logo.jpg', width=150)

if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- PRODUCTOS DE TU NEGOCIO ---
# He añadido tus líneas de negocio: imanes y corte láser
productos = [
    {"id": 1, "nombre": "Imán Souvenir Ciudad", "precio": 12000, "img": "https://via.placeholder.com/150?text=Iman"},
    {"id": 2, "nombre": "Diseño Corte Láser Personalizado", "precio": 35000, "img": "https://via.placeholder.com/150?text=Laser"},
    {"id": 3, "nombre": "Molde 3D para Imanes", "precio": 25000, "img": "https://via.placeholder.com/150?text=Molde"}
]

# --- FUNCIÓN DE FACTURA PDF CON LOGO ---
def generar_pdf(nombre_cliente, items):
    pdf = FPDF()
    pdf.add_page()
    
    # Logo en el PDF
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

    # Encabezados de tabla
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(140, 10, " Concepto", border=1, fill=True)
    pdf.cell(40, 10, " Precio", border=1, ln=True, fill=True)
    
    pdf.set_font("Arial", size=11)
    total = 0
    for item in items:
        pdf.cell(140, 10, f" {item['nombre']}", border=1)
        pdf.cell(40, 10, f" ${item['precio']}", border=1, ln=True)
        total += item['precio']
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, "TOTAL", border=0)
    pdf.cell(40, 10, f"${total}", border=0, ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
st.title("Catálogo Digital")
st.write("Selecciona los productos para generar tu cotización o factura.")

c1, c2 = st.columns([2, 1])

with c1:
    cols = st.columns(3)
    for i, p in enumerate(productos):
        with cols[i % 3]:
            st.image(p['img'], use_container_width=True)
            st.markdown(f"**{p['nombre']}**")
            st.write(f"${p['precio']}")
            if st.button(f"Agregar", key=f"btn_{p['id']}"):
                st.session_state.carrito.append(p)
                st.success("Añadido")

with c2:
    st.subheader("Tu Selección")
    if st.session_state.carrito:
        total = 0
        for item in st.session_state.carrito:
            st.text(f"• {item['nombre']} (${item['precio']})")
            total += item['precio']
        
        st.write(f"### Total: ${total}")
        nombre = st.text_input("Nombre del cliente")
        
        if nombre:
            pdf_bytes = generar_pdf(nombre, st.session_state.carrito)
            st.download_button(
                "📥 Descargar Factura PDF",
                data=pdf_bytes,
                file_name=f"factura_ZE_{nombre}.pdf",
                mime="application/pdf"
            )
        
        if st.button("Vaciar carrito"):
            st.session_state.carrito = []
            st.rerun()
    else:
        st.info("El carrito está vacío")
