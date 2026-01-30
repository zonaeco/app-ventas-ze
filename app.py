import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from fpdf import FPDF
import datetime
import re

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ZE - Gestión de Ventas", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
# ¡IMPORTANTE! Reemplaza este link por el tuyo y asegúrate de que sea PÚBLICO
url_hoja = "https://docs.google.com/spreadsheets/d/TU_ID_AQUÍ/edit?usp=sharing"

# Inicializamos variables para evitar errores de carga
df_actual = pd.DataFrame(columns=['id', 'nombre', 'precio', 'img'])

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_actual = conn.read(spreadsheet=url_hoja)
except Exception as e:
    st.error("⚠️ Error de conexión: No se pudo leer la hoja de Google Sheets.")
    st.info("Asegúrate de que la hoja esté compartida como 'Cualquier persona con el enlace puede leer'.")
    # Datos de respaldo para que la app no se rompa
    df_actual = pd.DataFrame([
        {"id": "001", "nombre": "Imán Prueba", "precio": 12000, "img": ""},
        {"id": "002", "nombre": "Corte Láser", "precio": 35000, "img": ""}
    ])

# --- FUNCIONES ---
def corregir_link_drive(url):
    if isinstance(url, str) and "drive.google.com" in url:
        drive_match = re.search(r'id=([a-zA-Z0-9_-]+)|/d/([a-zA-Z0-9_-]+)', url)
        if drive_match:
            file_id = drive_match.group(1) or drive_match.group(2)
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
    return url

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
    pdf.cell(140, 10, " TOTAL A PAGAR", border=0)
    pdf.cell(40, 10, f" ${total}", border=0, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- ESTADOS DE SESIÓN ---
if 'carrito' not in st.session_state:
    st.session_state.carrito = []
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False

# --- INTERFAZ ---
col_logo, _ = st.columns([1, 4])
with col_logo:
    if st.button("🔑"):
        st.session_state.admin_mode = not st.session_state.admin_mode
    st.image('logo.jpg', width=150)

# Panel Administrativo
if st.session_state.admin_mode:
    clave = st.text_input("Clave maestra", type="password")
    if clave == "1234":
        st.subheader("🛠️ Gestión de Inventario")
        df_editado = st.data_editor(df_actual, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Guardar cambios"):
            try:
                conn.update(spreadsheet=url_hoja, data=df_editado)
                st.success("¡Guardado!")
                st.rerun()
            except:
                st.error("Error al guardar. Verifica los permisos de EDITOR en la hoja.")
    st.divider()

# Catálogo Digital
st.title("Catálogo Digital ZE")
c1, c2 = st.columns([2, 1])

with c1:
    cols = st.columns(2)
    for i, row in df_actual.iterrows():
        with cols[i % 2]:
            img_url = corregir_link_drive(str(row.get('img', '')))
            st.image(img_url if img_url else "https://via.placeholder.com/150", use_container_width=True)
            st.subheader(row.get('nombre', 'Producto'))
            st.write(f"Código: {row.get('id', '000')} | **${row.get('precio', 0)}**")
            if st.button(f"Añadir", key=f"add_{i}"):
                st.session_state.carrito.append(row.to_dict())
                st.toast("Agregado")

with c2:
    st.subheader("🛒 Pedido")
    if st.session_state.carrito:
        total_p = sum(float(item.get('precio', 0)) for item in st.session_state.carrito)
        for item in st.session_state.carrito:
            st.text(f"• {item.get('nombre')} (${item.get('precio')})")
        st.write(f"### Total: ${total_p}")
        nom_c = st.text_input("Nombre del cliente")
        if nom_c:
            pdf_data = generar_pdf(nom_c, st.session_state.carrito)
            st.download_button("📥 Descargar Factura", data=pdf_data, file_name=f"ZE_{nom_c}.pdf")
        if st.button("Vaciar"):
            st.session_state.carrito = []
            st.rerun()
