import streamlit as st
from fpdf import FPDF
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ZE - Catálogo & Ventas", layout="wide")

# Inicializar el carrito de compras si no existe
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

# --- BASE DE DATOS (Simulada) ---
# Aquí podrías conectar tu base de datos real
productos = [
    {"id": 1, "nombre": "Imán Ciudad A", "precio": 15000, "stock": 10, "img": "https://via.placeholder.com/150"},
    {"id": 2, "nombre": "Imán Ciudad B", "precio": 15000, "stock": 5, "img": "https://via.placeholder.com/150"},
    {"id": 3, "nombre": "Corte Láser Personalizado", "precio": 45000, "stock": 2, "img": "https://via.placeholder.com/150"},
]

# --- FUNCIONES ---
def generar_pdf(nombre_cliente, items):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado con Logo
    # Nota: Asegúrate de tener 'logo_ze.jpg' en la misma carpeta
    try:
        pdf.image('image_b6e77d.jpg', x=10, y=8, w=30) 
    except:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "LOGOTIPO ZE", ln=True)

    pdf.ln(20)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "FACTURA DE VENTA", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Fecha: {datetime.date.today()}", ln=True)
    pdf.cell(0, 10, f"Cliente: {nombre_cliente}", ln=True)
    pdf.ln(10)

    # Tabla de productos
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(90, 10, "Producto", border=1)
    pdf.cell(40, 10, "Precio", border=1, ln=True)
    
    pdf.set_font("Arial", size=12)
    total = 0
    for item in items:
        pdf.cell(90, 10, item['nombre'], border=1)
        pdf.cell(40, 10, f"${item['precio']}", border=1, ln=True)
        total += item['precio']
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"TOTAL A PAGAR: ${total}", ln=True, align='R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
st.title("🛒 Catálogo de Productos ZE")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Selecciona tus piezas")
    # Crear una cuadrícula para los productos
    cols_prod = st.columns(3)
    for i, p in enumerate(productos):
        with cols_prod[i % 3]:
            st.image(p['img'], use_container_width=True)
            st.write(f"**{p['nombre']}**")
            st.write(f"Precio: ${p['precio']}")
            if st.button(f"Añadir", key=p['id']):
                st.session_state.carrito.append(p)
                st.toast(f"{p['nombre']} añadido")

with col2:
    st.subheader("Tu Pedido")
    if not st.session_state.carrito:
        st.info("El carrito está vacío")
    else:
        total_pago = 0
        for i, item in enumerate(st.session_state.carrito):
            st.write(f"- {item['nombre']} (${item['precio']})")
            total_pago += item['precio']
        
        st.divider()
        st.write(f"### Total: ${total_pago}")
        
        nombre = st.text_input("Nombre del Cliente")
        
        if st.button("Limpiar Carrito"):
            st.session_state.carrito = []
            st.rerun()

        if nombre and st.session_state.carrito:
            pdf_bytes = generar_pdf(nombre, st.session_state.carrito)
            st.download_button(
                label="📥 Descargar Factura PDF",
                data=pdf_bytes,
                file_name=f"factura_{nombre}.pdf",
                mime="application/pdf"
            )
