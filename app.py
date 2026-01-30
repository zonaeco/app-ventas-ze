import streamlit as st
from fpdf import FPDF
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# Inicializar estados si no existen
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False
if 'productos' not in st.session_state:
    # Productos iniciales
    st.session_state.productos = [
        {"id": 1, "nombre": "Imán Souvenir Ciudad", "precio": 12000},
        {"id": 2, "nombre": "Diseño Corte Láser Personalizado", "precio": 35000},
        {"id": 3, "nombre": "Molde 3D para Imanes", "precio": 25000}
    ]

# --- ESTILOS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 5px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- CABECERA Y LOGO (BOTÓN OCULTO) ---
col_logo, col_vacio = st.columns([1, 4])
with col_logo:
    # Al hacer clic en la imagen, activamos el modo login
    if st.button("🔑", help="Acceso Administrativo", key="logo_btn"):
        st.session_state.admin_mode = not st.session_state.admin_mode

    st.image('logo.jpg', width=150)

# --- SISTEMA DE LOGIN ---
if st.session_state.admin_mode:
    st.divider()
    with st.expander("🔐 Panel de Administración", expanded=True):
        password = st.text_input("Introduce la clave maestra", type="password")
        if password == "1234": # <--- CAMBIA TU CLAVE AQUÍ
            st.success("Acceso concedido")
            
            st.subheader("Modificar Inventario")
            for i, p in enumerate(st.session_state.productos):
                col_n, col_p = st.columns(2)
                with col_n:
                    new_name = st.text_input(f"Nombre #{p['id']}", value=p['nombre'], key=f"name_{i}")
                with col_p:
                    new_price = st.number_input(f"Precio #{p['id']}", value=p['precio'], key=f"price_{i}")
                
                st.session_state.productos[i]['nombre'] = new_name
                st.session_state.productos[i]['precio'] = new_price
            
            if st.button("Cerrar Sesión"):
                st.session_state.admin_mode = False
                st.rerun()
        elif password:
            st.error("Clave incorrecta")
    st.divider()

# --- FUNCIÓN PDF ---
def generar_pdf(nombre_cliente, items):
    pdf = FPDF()
    pdf.add_page()
    try:
        pdf.image('logo.jpg', x=10, y=8, w=30)
    except: pass
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "FACTURA DE VENTA - ZE", ln=True, align='C')
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 10, f"Fecha: {datetime.date.today()}", ln=True)
    pdf.cell(0, 10, f"Cliente: {nombre_cliente}", ln=True)
    pdf.ln(10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(140, 10, " Concepto", border=1, fill=True)
    pdf.cell(40, 10, " Precio", border=1, ln=True, fill=True)
    total = 0
    for item in items:
        pdf.cell(140, 10, f" {item['nombre']}", border=1)
        pdf.cell(40, 10, f" ${item['precio']}", border=1, ln=True)
        total += item['precio']
    pdf.ln(5)
    pdf.cell(140, 10, "TOTAL", border=0)
    pdf.cell(40, 10, f"${total}", border=0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- CUERPO DE LA APP ---
st.title("Catálogo Digital")
c1, c2 = st.columns([2, 1])

with c1:
    cols = st.columns(3)
    for i, p in enumerate(st.session_state.productos):
        with cols[i % 3]:
            # Imagen genérica mientras subes las tuyas
            st.image("https://via.placeholder.com/150", use_container_width=True)
            st.markdown(f"**{p['nombre']}**")
            st.write(f"${p['precio']}")
            if st.button(f"Agregar", key=f"btn_{i}"):
                st.session_state.carrito.append(p)
                st.toast(f"Añadido: {p['nombre']}")

with c2:
    st.subheader("🛒 Tu Selección")
    if st.session_state.carrito:
        total = 0
        for item in st.session_state.carrito:
            st.text(f"• {item['nombre']} (${item['precio']})")
            total += item['precio']
        st.write(f"### Total: ${total}")
        nombre = st.text_input("Nombre del cliente")
        if nombre:
            pdf_bytes = generar_pdf(nombre, st.session_state.carrito)
            st.download_button("📥 Descargar Factura", data=pdf_bytes, file_name=f"ZE_{nombre}.pdf")
        if st.button("Vaciar carrito"):
            st.session_state.carrito = []
            st.rerun()
    else:
        st.info("El carrito está vacío")
