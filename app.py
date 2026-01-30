import streamlit as st
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ZE - Gestión de Inventario", layout="wide")

# --- FUNCIÓN PARA LIMPIAR LINKS DE DRIVE ---
def corregir_link_drive(url):
    # Detecta si es un link de Google Drive y extrae el ID
    drive_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
    if drive_match:
        file_id = drive_match.group(1) or drive_match.group(2)
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    return url

# Inicializar estados
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False
if 'productos' not in st.session_state:
    st.session_state.productos = [
        {"id": "001", "nombre": "Imán Souvenir", "precio": 12000, "img": "https://via.placeholder.com/150"},
    ]

# --- ESTILOS ---
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .producto-card { border: 1px solid #eee; padding: 15px; border-radius: 12px; background: white; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- CABECERA ---
col_logo, _ = st.columns([1, 4])
with col_logo:
    if st.button("🔑", help="Panel Admin"):
        st.session_state.admin_mode = not st.session_state.admin_mode
    st.image('logo.jpg', width=150)

# --- PANEL ADMINISTRATIVO ---
if st.session_state.admin_mode:
    st.divider()
    with st.expander("🛠️ Administrador de Catálogo", expanded=True):
        password = st.text_input("Clave", type="password")
        if password == "1234":
            st.success("Modo edición activo")
            
            # Editar productos existentes
            for i, p in enumerate(st.session_state.productos):
                c1, c2, c3, c4, c5 = st.columns([1, 2, 1, 3, 1])
                with c1: st.text_input("Cod", value=p['id'], key=f"id_{i}")
                with c2: st.text_input("Nombre", value=p['nombre'], key=f"name_{i}")
                with c3: st.number_input("Precio", value=p['precio'], key=f"price_{i}")
                with c4: 
                    raw_url = st.text_input("URL Imagen / Drive", value=p['img'], key=f"img_{i}")
                    # Aplicar corrección automática
                    st.session_state.productos[i]['img'] = corregir_link_drive(raw_url)
                with c5:
                    if st.button("🗑️", key=f"del_{i}"):
                        st.session_state.productos.pop(i)
                        st.rerun()
            
            st.divider()
            if st.button("➕ Añadir Nuevo Producto"):
                nuevo = {"id": "NUEVO", "nombre": "Nuevo Item", "precio": 0, "img": "https://via.placeholder.com/150"}
                st.session_state.productos.append(nuevo)
                st.rerun()

# --- CATÁLOGO ---
st.title("Catálogo de Diseños")
c_cat, c_ped = st.columns([2, 1])

with c_cat:
    prod_cols = st.columns(2)
    for i, p in enumerate(st.session_state.productos):
        with prod_cols[i % 2]:
            st.markdown(f'<div class="producto-card">', unsafe_allow_html=True)
            st.image(p['img'], use_container_width=True)
            st.subheader(p['nombre'])
            st.write(f"Código: {p['id']} | **${p['precio']}**")
            if st.button(f"Seleccionar", key=f"add_{i}"):
                st.session_state.carrito.append(p)
                st.toast(f"Agregado: {p['nombre']}")
            st.markdown('</div>', unsafe_allow_html=True)

# --- CARRITO Y FACTURA ---
with c_ped:
    st.subheader("🛒 Pedido")
    if st.session_state.carrito:
        total = sum(item['precio'] for item in st.session_state.carrito)
        for item in st.session_state.carrito:
            st.text(f"• {item['nombre']} (${item['precio']})")
        st.write(f"### Total: ${total}")
        
        nombre_cliente = st.text_input("Nombre del cliente")
        if nombre_cliente:
            # (Aquí iría tu función generar_pdf que ya tienes)
            st.button("📥 Generar Factura") # Botón de ejemplo
            
        if st.button("Limpiar Pedido"):
            st.session_state.carrito = []
            st.rerun()
