import streamlit as st
import time
import os
from dotenv import load_dotenv
import urllib.parse

# Módulos personalizados
from auth_utils import verify_login
from pdf_generator import generar_pdf_viaje

# Configuración de la página DEBE ser el primer comando de Streamlit
st.set_page_config(page_title="Sistema de Logística", layout="wide")

# Cargar variables de entorno
load_dotenv()

st.title("Sistema de Gestión de Viajes y Logística")

# Importación segura de módulos
try:
    import pandas as pd
    from sqlalchemy.orm import sessionmaker
    from datetime import datetime, date, timedelta
    from modelos import engine, Usuario, Viaje, Vehiculo, Base
    from limpiador_excel import procesar_excel
except Exception as e:
    st.error(f"Error crítico al importar módulos: {e}")
    st.stop()

# Configurar sesión de base de datos
# --- CRUCIAL: Asegurar que las tablas existen (especialmente en la nube) ---
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def get_test_user(rol, session):
    nombre = f"Usuario {rol}"
    correo = f"{rol.lower()}@test.com"
    user = session.query(Usuario).filter_by(correo_google=correo).first()
    if not user:
        user = Usuario(nombre_completo=nombre, correo_google=correo, rol=rol, activo=True)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

def generar_link_calendar(viaje):
    """Genera un enlace para crear un evento en Google Calendar."""
    titulo = f"Viaje a {viaje.destino_limpio} - {viaje.proyecto}"
    
    fmt = "%Y%m%d"
    inicio_str = viaje.fecha_inicio.strftime(fmt)
    fin_real = viaje.fecha_fin + timedelta(days=1)
    fin_str = fin_real.strftime(fmt)
    
    descripcion = f"Proyecto: {viaje.proyecto}\n"
    descripcion += f"Personal: {viaje.personal_asignado}\n"
    descripcion += f"Vehículos/Obs: {viaje.observaciones_vehiculo}\n"
    descripcion += f"Detalles: {viaje.breve_descripcion}\n"
    
    params = {
        "action": "TEMPLATE",
        "text": titulo,
        "dates": f"{inicio_str}/{fin_str}",
        "details": descripcion,
        "location": viaje.destino_limpio,
        "add": viaje.correo_trabajador 
    }
    
    base_url = "https://calendar.google.com/calendar/render"
    query_string = urllib.parse.urlencode(params)
    return f"{base_url}?{query_string}"

def main():
    # --- AUTENTICACIÓN ---
    if 'usuario_autenticado' not in st.session_state:
        st.session_state['usuario_autenticado'] = None

    if not st.session_state['usuario_autenticado']:
        st.markdown("## 🔐 Acceso al Sistema de Logística")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                st.subheader("Iniciar Sesión")
                username = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Entrar")
                
                if submit:
                    user_info = verify_login(username, password)
                    if user_info:
                        st.session_state['usuario_autenticado'] = user_info
                        st.success(f"Bienvenido {user_info['name']}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
            
            st.info("**Credenciales de Acceso:**\n\nSolicite las credenciales al administrador del sistema.")
        return

    # --- SI ESTÁ LOGUEADO ---
    usuario_info = st.session_state['usuario_autenticado']
    rol_seleccionado = usuario_info['role']
    
    # Barra lateral
    with st.sidebar:
        st.write(f"👤 **{usuario_info['name']}**")
        st.write(f"🔑 Rol: {rol_seleccionado}")
        
        if st.button("Cerrar Sesión"):
            st.session_state['usuario_autenticado'] = None
            st.rerun()
            
        st.divider()

    try:
        session = get_session()
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        return
    
    # Lógica de Roles
    if rol_seleccionado == "Admin":
        vista_admin(session)
            
    elif rol_seleccionado == "Trabajador":
        usuario_actual = get_test_user("Trabajador", session)
        
        # Input de Correo Persistente
        correo_key = f"correo_{usuario_actual.id}"
        if correo_key not in st.session_state:
             st.session_state[correo_key] = ""
             
        correo_input = st.sidebar.text_input("Tu Correo (Notificaciones)", value=st.session_state[correo_key], placeholder="ejemplo@gmail.com")
        if correo_input:
            st.session_state['correo_trabajador'] = correo_input
            st.session_state[correo_key] = correo_input
        
        vista_trabajador(session, usuario_actual)
    
    session.close()

def vista_trabajador(session, usuario):
    st.header("Mis Viajes - Panel de Trabajador")
    
    tab1, tab2 = st.tabs(["📂 Carga Masiva (Excel)", "📝 Solicitud Manual"])
    
    with tab1:
        st.subheader("Subir Excel de Viajes")
        uploaded_file = st.file_uploader("Arrastra tu archivo aquí", type=["xlsx"])
        
        if uploaded_file:
            try:
                temp_filename = f"temp_upload_{usuario.id}.xlsx"
                with open(temp_filename, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if st.button("Procesar y Guardar Excel"):
                    correo_notif = st.session_state.get('correo_trabajador', '').strip()
                    if not correo_notif:
                        st.warning("⚠️ Debes ingresar tu correo en la barra lateral antes de guardar.")
                    else:
                        try:
                            datos_limpios = procesar_excel(temp_filename)
                            count = 0
                            for fila in datos_limpios:
                                nuevo_viaje = Viaje(
                                    creador_id=usuario.id,
                                    proyecto=fila.get('origen', 'Origen Desconocido'), 
                                    destino_limpio=fila['destino_limpio'],
                                    personal_asignado=fila['personal_asignado'],
                                    fecha_inicio=fila['fecha_inicio'],
                                    fecha_fin=fila['fecha_fin'],
                                    estado_viaje='Pendiente de Asignación',
                                    correo_trabajador=correo_notif
                                )
                                session.add(nuevo_viaje)
                                count += 1
                            session.commit()
                            st.success(f"Se han insertado {count} viajes correctamente.")
                            time.sleep(1) 
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error procesando datos: {e}")
                        finally:
                            if os.path.exists(temp_filename):
                                os.remove(temp_filename)
            except Exception as e:
                st.error(f"Error al subir el archivo: {e}")

    with tab2:
        st.subheader("Registrar Nuevo Viaje Manualmente")
        with st.form("form_viaje_manual"):
            col1, col2 = st.columns(2)
            with col1:
                proyecto = st.text_input("Proyecto / Origen", placeholder="Ej. Instalación QRO")
                destino = st.text_input("Destino", placeholder="Ej. Querétaro")
                personal = st.text_area("Personal Asignado", placeholder="Juan Perez, Maria Lopez...")
            with col2:
                fecha_inicio = st.date_input("Fecha Inicio", min_value=date.today())
                fecha_fin = st.date_input("Fecha Fin", min_value=date.today())
            
            breve_descripcion = st.text_area("Breve Descripción del Viaje", height=100, placeholder="Detalles de logística, horarios específicos, etc.")
            observaciones_vehiculo = st.text_input("Vehículos y Observaciones solicitadas", placeholder="Ej. 1 Camioneta, 1 Grúa, herramientas especiales...")

            submitted = st.form_submit_button("Solicitar Viaje")
            
            if submitted:
                correo_notif = st.session_state.get('correo_trabajador', '').strip()
                
                if not correo_notif:
                    st.warning("⚠️ Debes ingresar tu correo en la barra lateral antes de solicitar un viaje.")
                elif not proyecto or not destino or not personal or not breve_descripcion or not observaciones_vehiculo:
                    st.error("⚠️ Por favor completa TODOS los campos.")
                elif fecha_fin < fecha_inicio:
                    st.error("⛔ La fecha de fin no puede ser anterior a la de inicio.")
                else:
                    try:
                        nuevo_viaje = Viaje(
                            creador_id=usuario.id,
                            proyecto=proyecto,
                            destino_limpio=destino, 
                            personal_asignado=personal,
                            fecha_inicio=fecha_inicio,
                            fecha_fin=fecha_fin,
                            estado_viaje='Pendiente de Asignación',
                            breve_descripcion=breve_descripcion,
                            observaciones_vehiculo=observaciones_vehiculo,
                            correo_trabajador=correo_notif
                        )
                        session.add(nuevo_viaje)
                        session.commit()
                        st.success("✅ ¡Solicitud de viaje registrada exitosamente!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar en base de datos: {e}")

    st.subheader("Historial de Viajes Solicitados")
    
    filtro_historial = st.radio("Mostrar:", ["Pendientes de Asignación", "Historial Completo"], horizontal=True)
    
    query_base = session.query(Viaje).filter_by(creador_id=usuario.id).order_by(Viaje.id_viaje.desc())
    
    if filtro_historial == "Pendientes de Asignación":
        mis_viajes = query_base.filter_by(estado_viaje='Pendiente de Asignación').all()
    else:
        mis_viajes = query_base.all()
    
    if mis_viajes:
        for v in mis_viajes:
            icono = "⏳" if v.estado_viaje == 'Pendiente de Asignación' else "✅" if v.estado_viaje == 'Proyectado' else "🚗"
            
            with st.expander(f"{icono} Viaje #{v.id_viaje} | {v.destino_limpio} ({v.fecha_inicio})"):
                if v.estado_viaje == 'Pendiente de Asignación':
                    st.info("Este viaje aún no ha sido asignado, puedes modificarlo.")
                    
                    with st.form(key=f"edit_viaje_{v.id_viaje}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_proyecto = st.text_input("Proyecto", value=v.proyecto)
                            new_destino = st.text_input("Destino", value=v.destino_limpio)
                            new_personal = st.text_area("Personal", value=v.personal_asignado)
                        with col2:
                            new_fecha_inicio = st.date_input("Inicio", value=v.fecha_inicio)
                            new_fecha_fin = st.date_input("Fin", value=v.fecha_fin)
                        
                        new_desc = st.text_area("Descripción", value=v.breve_descripcion or "")
                        new_obs = st.text_input("Vehículos/Obs", value=v.observaciones_vehiculo or "")
                        
                        save = st.form_submit_button("💾 Guardar Cambios")
                        
                        if save:
                            v.proyecto = new_proyecto
                            v.destino_limpio = new_destino
                            v.personal_asignado = new_personal
                            v.fecha_inicio = new_fecha_inicio
                            v.fecha_fin = new_fecha_fin
                            v.breve_descripcion = new_desc
                            v.observaciones_vehiculo = new_obs
                            session.commit()
                            st.success("Viaje actualizado correctamente.")
                            time.sleep(0.5)
                            st.rerun()
                    
                    if st.button(f"🗑️ Cancelar/Eliminar Viaje #{v.id_viaje}", key=f"del_{v.id_viaje}"):
                        session.delete(v)
                        session.commit()
                        st.warning("Viaje eliminado.")
                        time.sleep(0.5)
                        st.rerun()
                        
                else:
                    st.markdown(f"**Estado:** {v.estado_viaje}")
                    st.markdown(f"**Proyecto:** {v.proyecto}")
                    st.markdown(f"**Personal:** {v.personal_asignado}")
                    st.markdown(f"**Descripción:** {v.breve_descripcion}")
                    
                    if v.vehiculo_id:
                        vehiculo = session.query(Vehiculo).get(v.vehiculo_id)
                        if vehiculo:
                             st.success(f"🛻 **Vehículo Asignado:** {vehiculo.modelo} ({vehiculo.placas})")
                    else:
                        st.warning("Sin vehículo asignado aún.")

    else:
        st.info("No tienes viajes registrados en esta categoría.")

def vista_admin(session):
    st.header("Gestión de Flota - Panel de Administrador")
    
    vehiculos = session.query(Vehiculo).all()
    if not vehiculos:
        if st.button("Generar Vehículos de Prueba"):
            v1 = Vehiculo(modelo="Nissan Versa 2024", placas="ABC-123", estado="Disponible")
            v2 = Vehiculo(modelo="Toyota Hilux 4x4", placas="XYZ-789", estado="Disponible")
            session.add_all([v1, v2])
            session.commit()
            st.rerun()

    opciones_vehiculos = {v.id: f"{v.modelo} ({v.placas})" for v in vehiculos}
    
    filtro_estado = st.radio("Filtrar por estado:", ["Pendientes", "Todos"], horizontal=True)
    
    query = session.query(Viaje)
    if filtro_estado == "Pendientes":
        query = query.filter_by(estado_viaje='Pendiente de Asignación')
    
    viajes = query.order_by(Viaje.id_viaje.desc()).all()
    
    if not viajes:
        st.info("No hay viajes para mostrar con el filtro seleccionado.")
    else:
        st.write(f"Mostrando {len(viajes)} viajes.")
        for viaje in viajes:
            with st.expander(f"#{viaje.id_viaje} | {viaje.destino_limpio} | {viaje.fecha_inicio} ({viaje.estado_viaje})", expanded=(viaje.estado_viaje == 'Pendiente de Asignación')):
                with st.form(key=f"form_{viaje.id_viaje}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Solicitante ID:** {viaje.creador_id}")
                        st.markdown(f"📧 **Correo:** {viaje.correo_trabajador}")
                        st.markdown(f"**Proyecto:** {viaje.proyecto}")
                        st.markdown(f"**Personal:** {viaje.personal_asignado}")
                        st.markdown(f"**Fechas:** {viaje.fecha_inicio} a {viaje.fecha_fin}")
                    
                    with col2:
                        idx_vehiculo = 0
                        if viaje.vehiculo_id and viaje.vehiculo_id in opciones_vehiculos:
                            idx_vehiculo = list(opciones_vehiculos.keys()).index(viaje.vehiculo_id)
                        
                        id_vehiculo = st.selectbox(
                            "Asignar Vehículo", 
                            options=list(opciones_vehiculos.keys()) if opciones_vehiculos else [None], 
                            format_func=lambda x: opciones_vehiculos.get(x, "Sin vehículos"),
                            index=idx_vehiculo,
                            disabled=not opciones_vehiculos
                        )
                        
                        costo_toka = st.number_input("Costo Toka", min_value=0.0, value=viaje.costo_toka or 0.0)
                        costo_casetas = st.number_input("Costo Casetas", min_value=0.0, value=viaje.costo_casetas or 0.0)
                        costo_hospedaje = st.number_input("Costo Hospedaje", min_value=0.0, value=viaje.costo_hospedaje or 0.0)
                    
                    col_btn1, col_btn2 = st.columns([1, 4])
                    aprobar = col_btn1.form_submit_button("💾 Guardar y Aprobar")
                    
                    if aprobar:
                        if not id_vehiculo:
                            st.error("Debes seleccionar un vehículo.")
                        else:
                            viaje.vehiculo_id = id_vehiculo
                            viaje.costo_toka = costo_toka
                            viaje.costo_casetas = costo_casetas
                            viaje.costo_hospedaje = costo_hospedaje
                            viaje.estado_viaje = 'Proyectado'
                            session.commit()
                            st.success("¡Viaje actualizado y aprobado!")
                            
                            link_calendar = generar_link_calendar(viaje)
                            st.markdown(f"### 📅 [Haz clic aquí para agendar en Google Calendar]({link_calendar})")
                            st.info("El viaje ha cambiado a estado 'Proyectado'. Recarga la página para actualizar la lista.")
                            time.sleep(1)
                            st.rerun()

                # Botón de PDF fuera del formulario
                vehiculo_obj = session.query(Vehiculo).get(viaje.vehiculo_id) if viaje.vehiculo_id else None
                pdf_data = generar_pdf_viaje(viaje, vehiculo_obj)
                
                st.download_button(
                    label="📄 Descargar Reporte PDF",
                    data=pdf_data,
                    file_name=f"Viaje_{viaje.id_viaje}_Reporte.pdf",
                    mime="application/pdf",
                    key=f"pdf_{viaje.id_viaje}"
                )

if __name__ == "__main__":
    main()
