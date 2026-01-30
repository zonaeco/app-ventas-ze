import streamlit as st
from fpdf import FPDF
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ZE - Gestión de Inventario", layout="wide")

# Inicializar estados si no existen
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False
if 'productos' not in st.session_state:
    # Base de datos inicial con Código e Imagen
    st.session_state.productos = [
        {"id": "001", "nombre": "Imán Souvenir", "precio": 12000, "img": "https://via.placeholder.com/150"},
        {"id": "002", "nombre": "Corte Láser", "precio": 35000, "img": "https://via.placeholder.com/150"},
        {"id": "003", "nombre": "Molde 3D", "precio": 25000, "img": "https://via.placeholder.com/150"}
    ]

# --- ESTILOS PROFESIONALES ---
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stButton>button { border-radius: 8px; }
    .producto-card { border: 1px solid #eee; padding: 10px; border-radius: 10px; background: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CABECERA ---
col_logo, _ = st.columns([1, 4])
with col_logo:
    # El botón discreto para el admin
    if st.button("🔑", help="Administrar Productos", key="admin_key"):
        st.session_state.admin_mode = not st.session_state.admin_mode
    st.image('logo.jpg', width=150)

# --- PANEL ADMINISTRATIVO (MODIFICAR PRODUCTOS) ---
if st.session_state.admin_mode:
    st.divider()
    with st.expander("🛠️ Panel de Control de Inventario", expanded=True):
        password = st.text_input("Clave maestra", type="password")
        if password == "1234":
            st.success("Modo edición activado")
            
            # Formulario para editar cada producto
            for i, p in enumerate(st.session_state.productos):
                st.markdown(f"#### Editando Producto: {p['id']}")
                c1, c2, c3, c4 = st.columns([1, 2, 1, 2])
                with c1:
                    new_id = st.text_input("Código", value=p['id'], key=f"id_{i}")
                with c2:
                    new_name = st.text_input("Nombre", value=p['nombre'], key=f"name_{i}")
                with c3:
                    new_price = st.number_input("Precio", value=p['precio'], key=f"price_{i}")
                with c4:
                    new_img = st.text_input("URL Imagen", value=p['img'], key=f"img_{i}")
                
                # Actualizar datos en la sesión
                st.session_state.productos[i] = {
                    "id": new_id, "nombre": new_name, "precio": new_price, "img": new_img
                }
                st.divider()
            
            if st.button("Cerrar Sesión"):
                st.session_state.admin_mode = False
                st.rerun()
    st.divider()

# --- FUNCIÓN DE FACTURA ---
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
    
    # Tabla con código
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 10, " Cod.", border=1, fill=True)
    pdf.cell(110, 10, " Concepto", border=1, fill=True)
    pdf.cell(40, 10, " Precio", border=1, ln=True, fill=True)
    
    pdf.set_font("Arial", size=10)
    total = 0
    for item in items:
        pdf.cell(30, 10, f" {item['id']}", border=1)
        pdf.cell(110, 10, f" {item['nombre']}", border=1)
        pdf.cell(40, 10, f" ${item['precio']}", border=1, ln=True)
        total += item['precio']
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(140, 10, " TOTAL A PAGAR", border=0)
    pdf.cell(40, 10, f" ${total}", border=0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- CATÁLOGO PARA EL CLIENTE ---
st.title("Catálogo Digital de Diseños")

col_cat, col_cart = st.columns([2, 1])

with col_cat:
    # Mostrar productos en cuadrícula
    prod_cols = st.columns(2)
    for i, p in enumerate(st.session_state.productos):
        with prod_cols[i % 2]:
            st.markdown(f"""
            <div class="producto-card">
                <small>Código: {p['id']}</small>
                <h4>{p['nombre']}</h4>
            </div>
            """, unsafe_allow_html=True)
            st.image(p['img'], use_container_width=True)
            st.write(f"**Precio:** ${p['precio']}")
            if st.button(f"Añadir al pedido", key=f"add_{i}"):
                st.session_state.carrito.append(p)
                st.toast(f"Añadido: {p['nombre']}")

with col_cart:
    st.subheader("🛒 Pedido Actual")
    if st.session_state.carrito:
        total_venta = 0
        for item in st.session_state.carrito:
            st.text(f"[{item['id']}] {item['nombre']} - ${item['precio']}")
            total_venta += item['precio']
        
        st.write(f"### Total: ${total_venta}")
        nombre_c = st.text_input("Nombre Completo del Cliente")
        
        if nombre_c:
            factura_pdf = generar_pdf(nombre_c, st.session_state.carrito)
            st.download_button(
                label="📥 Generar Factura con Logo",
                data=factura_pdf,
                file_name=f"Factura_ZE_{nombre_c}.pdf",
                mime="application/pdf"
            )
        
        if st.button("Limpiar selección"):
            st.session_state.carrito = []
            st.rerun()
    else:
        st.info("Selecciona piezas del catálogo")
