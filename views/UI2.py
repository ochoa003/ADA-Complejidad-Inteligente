# UI.py
# Interfaz Streamlit para el Analizador de Complejidad:
# - Orquesta entrada del usuario (pseudocódigo o descripción natural).
# - Mide y muestra tiempos de ejecución del analizador local y del LLM (segundos).
# - Renderiza resultados en tres pestañas: análisis, opinión LLM y diagrama DOT.
# - Mantiene historial con texto y gráficos para revisión posterior.

import sys
import os
import json
import streamlit as st
import time  # Medición de latencias (analizador, LLM y diagrama)

# Ajuste de paths
# Añade la carpeta raíz del proyecto al sys.path para que los imports relativos funcionen
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.analizador import analizar_complejidad
from helpers.llm_helper2 import configurar_llm, obtener_analisis_llm, traducir_a_pseudocodigo, generar_diagrama_dot

# Importar ejemplos de pseudocódigo para pruebas rápidas desde el sidebar
# Se usa try/except para evitar que la UI falle si el módulo data/pruebas no existe
try:
    from data.pruebas import (
        algo_constante, algo_lineal, algo_cuadratico, algo_condicional, algo_while_lineal,
        algo_repeat_log, algo_busqueda_binaria, algo_merge_sort, algo_busqueda_arreglo,
        algo_con_declaraciones, algo_lineal_con_declaraciones, algo_call_o1, algo_call_on,
        algo_call_anidado, algo_call_merge_sort_detallado, algo_for_n2, algo_cubico,
        algo_while_log, algo_for_con_log_interno, algo_if_balanceado, algo_for_length_m,
        algo_for_y_for_interno, algo_repeat_log_base3, algo_while_length, algo_call_swap_n2,
        algo_mixto_call_y_log, algo_if_pesado, algo_for_m, algo_for_n_y_m, algo_recursion_3_llamadas,
        algo_dp_1d, algo_dp_2d, algo_dp_memo_1d, algo_dp_memo_2d, algo_dp_2d_n2, algo_dp_1d_log,
        algo_bnb_subsets, algo_bnb_tsp, algo_bnb_knapsack
    )
    # Mapa legible en UI: nombre descriptivo -> contenido del ejemplo
    EJEMPLOS_DICT = {
        "Prueba 1: Algoritmo Constante": algo_constante,
        "Prueba 2: Algoritmo Lineal (FOR)": algo_lineal,
        "Prueba 3: Algoritmo Cuadrático (FOR anidado)": algo_cuadratico,
        "Prueba 4: Condicional (Mejor/Peor)": algo_condicional,
        "Prueba 5: While lineal": algo_while_lineal,
        "Prueba 6: Repeat logarítmico": algo_repeat_log,
        "Prueba 7: Búsqueda Binaria Recursiva": algo_busqueda_binaria,
        "Prueba 8: Merge Sort (simplificado)": algo_merge_sort,
        "Prueba 9: Búsqueda lineal en arreglo": algo_busqueda_arreglo,
        "Prueba 10: Declaraciones de variables/objetos": algo_con_declaraciones,
        "Prueba 11: Lineal con declaraciones": algo_lineal_con_declaraciones,
        "Prueba 12: For con CALL O(1)": algo_call_o1,
        "Prueba 13: For con CALL O(n)": algo_call_on,
        "Prueba 14: For anidado con CALL O(1)": algo_call_anidado,
        "Prueba 15: Merge Sort detallado (CALL O(n))": algo_call_merge_sort_detallado,
        "Prueba 16: For hasta n^2": algo_for_n2,
        "Prueba 17: Triple bucle (cúbico)": algo_cubico,
        "Prueba 18: While halving (log n)": algo_while_log,
        "Prueba 19: For con log interno": algo_for_con_log_interno,
        "Prueba 20: If-else equilibrado": algo_if_balanceado,
        "Prueba 21: For sobre length(B)": algo_for_length_m,
        "Prueba 22: Doble for n y n": algo_for_y_for_interno,
        "Prueba 23: Repeat base 3 (log n)": algo_repeat_log_base3,
        "Prueba 24: While hasta length(A)": algo_while_length,
        "Prueba 25: CALL swap en n^2": algo_call_swap_n2,
        "Prueba 26: CALL O(n) + log interno": algo_mixto_call_y_log,
        "Prueba 27: If n^2 vs O(1)": algo_if_pesado,
        "Prueba 28: For hasta m": algo_for_m,
        "Prueba 29: For n y m (O(n*m))": algo_for_n_y_m,
        "Prueba 30: Recursión 3 llamadas + trabajo lineal": algo_recursion_3_llamadas,
        "DP 1: Tabla 1D (O(n))": algo_dp_1d,
        "DP 2: Tabla 2D (O(n*m))": algo_dp_2d,
        "DP 3: Memoización 1D": algo_dp_memo_1d,
        "DP 4: Memoización 2D": algo_dp_memo_2d,
        "DP 5: 2D n x n (O(n^2))": algo_dp_2d_n2,
        "DP 6: 1D con while log (O(n log n))": algo_dp_1d_log,
        "BnB 1: Subconjuntos con poda": algo_bnb_subsets,
        "BnB 2: TSP con poda": algo_bnb_tsp,
        "BnB 3: Knapsack con poda + n/2": algo_bnb_knapsack,
    }
except Exception:
    # Si falla la importación, la UI sigue operativa (solo sin ejemplos precargados)
    EJEMPLOS_DICT = {}

# ---------------------------
# Configuración de Página y CSS
# ---------------------------
st.set_page_config(
    page_title="ADA · Analizador de Complejidad",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
:root {
  --bg: #0f172a; --panel: #111827; --accent: #22d3ee; --accent-2: #60a5fa;
  --text: #e5e7eb; --muted: #9ca3af; --success: #22c55e; --warning: #f59e0b; --error: #ef4444;
}
html, body, [data-testid="stAppViewContainer"] { background-color: var(--bg); }
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3, h4, h5, h6, p, code, pre, .stTextInput, .stMarkdown { color: var(--text) !important; }
a { color: var(--accent) !important; }
.app-title {
  font-weight: 800; font-size: 2.2rem;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.section-title { font-weight: 700; font-size: 1.1rem; color: var(--muted); margin-top: 6px; }
.badge {
  display: inline-block; padding: 6px 10px; border-radius: 999px; font-size: 0.8rem;
  border: 1px solid #1f2937; background: #0b1222; color: var(--muted); margin-right: 8px;
}
.badge-ok { color: var(--success); border-color: var(--success); }
.badge-warn { color: var(--warning); border-color: var(--warning); }
.badge-err { color: var(--error); border-color: var(--error); }
.stTabs [role="tablist"] button { color: var(--muted); border-radius: 12px; }
.stTabs [role="tablist"] button[aria-selected="true"] { background: #0b1222; color: var(--text); border: 1px solid #1f2937; }
pre code, .stCodeBlock { background: #0b1222 !important; border: 1px solid #1f2937 !important; border-radius: 12px !important; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea { background: #0b1222; color: var(--text); border: 1px solid #1f2937; border-radius: 12px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.markdown('<div class="app-title">ADA</div>', unsafe_allow_html=True)
    st.caption("Analizador de Complejidad Algorítmica asistido por LLM")

    api_key = configurar_llm()
    if api_key:
        st.markdown('<span class="badge badge-ok">API Key detectada</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-err">API Key ausente</span>', unsafe_allow_html=True)

    st.markdown("---")
    es_lenguaje_natural = st.toggle("Entrada en lenguaje natural", value=False)
    st.markdown("---")
    st.info("Consejos:\n- Usa descripciones claras\n- Evita texto redundante\n- Mantén la gramática del pseudocódigo")

# ---------------------------
# Header
# ---------------------------
st.markdown('<div class="app-title">Analizador de Complejidad Algorítmica</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Ingresa tu pseudocódigo o descripción.</div>', unsafe_allow_html=True)

# ---------------------------
# Historial
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.expander("Historial de interacción", expanded=False):
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            content = message["content"]
            
            # CASO 1: El mensaje es un diccionario (Nuevo formato con gráfico)
            if isinstance(content, dict):
                # Mostrar texto
                if "text" in content and content["text"]:
                    st.markdown(content["text"])
                
                # Mostrar gráfico si existe
                if "dot_code" in content and content["dot_code"]:
                    try:
                        st.graphviz_chart(content["dot_code"])
                        with st.expander("Ver código DOT fuente"):
                            st.code(content["dot_code"], language="dot")
                    except Exception:
                        st.error("Error visualizando el gráfico del historial")
            
            # CASO 2: El mensaje es solo texto (Formato antiguo)
            elif isinstance(content, str):
                st.markdown(content)

st.markdown("---")

# ---------------------------
# Lógica de Entrada (Inputs y Botones)
# ---------------------------

def cargar_ejemplo_seleccionado():
    seleccion = st.session_state.selector_ejemplos_key
    if seleccion and seleccion in EJEMPLOS_DICT:
        st.session_state.prompt_input = EJEMPLOS_DICT[seleccion].strip()

def limpiar_callback():
    st.session_state.prompt_input = ""
    # Opcional: limpiar mensajes también si quieres
    # st.session_state.messages = [] 
    st.toast("Entrada limpiada")

if "prompt_input" not in st.session_state:
    st.session_state.prompt_input = ""

col_input = st.columns([3, 2])
with col_input[0]:
    prompt = st.text_area(
        "Contenido",
        key="prompt_input",
        placeholder="Ej: algoritmo con ciclos anidados; o pega tu pseudocódigo begin/end...",
        height=160
    )

with col_input[1]:
    st.markdown("##### Ejemplos")
    if EJEMPLOS_DICT:
        ejemplo_sel = st.selectbox(
            "Seleccionar ejemplo",
            options=list(EJEMPLOS_DICT.keys()),
            key="selector_ejemplos_key"
        )
        st.button("Insertar ejemplo", use_container_width=True, on_click=cargar_ejemplo_seleccionado)

# Botones de Acción
col_actions = st.columns([1, 1, 6])
with col_actions[0]:
    run_btn = st.button("Analizar", type="primary", use_container_width=True)
with col_actions[1]:
    # Botón limpiar con callback para evitar el error de session_state
    clear_btn = st.button("Limpiar", use_container_width=True, on_click=limpiar_callback)

# Frenar ejecución si no se pulsa Analizar
if not run_btn:
    st.stop()

prompt_val = st.session_state.prompt_input.strip()
if not prompt_val:
    st.error("Ingresa una descripción para continuar.")
    st.stop()

# ---------------------------
# Procesamiento y Guardado
# ---------------------------

# 1. Guardar mensaje del usuario (texto plano)
user_message = f"**Entrada del usuario:**\n```plaintext\n{prompt_val}\n```"
st.session_state.messages.append({"role": "user", "content": user_message})
with st.chat_message("user"):
    st.markdown(user_message)

with st.chat_message("assistant"):
    # Variables para construir la respuesta final estructurada
    texto_acumulado_respuesta = ""
    codigo_dot_para_historial = None
    
    codigo_a_analizar = prompt_val

    # A. Traducción
    if es_lenguaje_natural and api_key:
        start_time_trad = time.perf_counter()
        with st.spinner("Traduciendo..."):
            codigo_traducido = traducir_a_pseudocodigo(api_key, prompt_val)
        end_time_trad = time.perf_counter()
        translation_time = end_time_trad - start_time_trad
        
        st.markdown(f"### 🔄 Traducción <span class='badge' style='color: var(--muted);'>Tiempo: {translation_time:.2f}s</span>", unsafe_allow_html=True)

        if "❌" in codigo_traducido:
            st.error(codigo_traducido)
            st.stop()
        st.code(codigo_traducido, language="plaintext")
        codigo_a_analizar = codigo_traducido
        texto_acumulado_respuesta += f"**🔄 Pseudocódigo Traducido:**\n```plaintext\n{codigo_a_analizar}\n```\n\n"
    else:
        texto_acumulado_respuesta += f"**Pseudocódigo Analizado:**\n```plaintext\n{codigo_a_analizar}\n```\n\n"

    # B. Tabs de Resultados
    tab1, tab2, tab3 = st.tabs(["📊 Análisis", "🤖 Opinión del LLM", "🕸️ Diagrama"])

    # Tab 1: Análisis Estático
    with tab1:
        start_time_ast = time.perf_counter()
        try:
            resultado = analizar_complejidad(codigo_a_analizar)
            formatted_result = json.dumps(resultado, indent=2, ensure_ascii=False)
            status_ok = True
        except Exception as e:
            formatted_result = f"Error: {e}"
            status_ok = False
        end_time_ast = time.perf_counter()
        analyzer_time = end_time_ast - start_time_ast

        st.markdown(f"#### Análisis Estático <span class='badge' style='color: var(--muted);'>Tiempo: {analyzer_time:.4f}s</span>", unsafe_allow_html=True)
        
        if status_ok:
            st.code(formatted_result, language="json")
            texto_acumulado_respuesta += f"**📊 Análisis del Sistema:**\n```json\n{formatted_result}\n```\n\n"
        else:
            st.error(formatted_result)
            texto_acumulado_respuesta += f"**Error Análisis:** {formatted_result}\n\n"

    # Tab 2: LLM
    with tab2:
        if api_key:
            start_time_llm = time.perf_counter()
            with st.spinner("Consultando LLM..."):
                analisis_llm = obtener_analisis_llm(api_key, codigo_a_analizar)
            end_time_llm = time.perf_counter()
            llm_time = end_time_llm - start_time_llm
            
            st.markdown(f"#### Opinión del Experto <span class='badge' style='color: var(--muted);'>Tiempo: {llm_time:.2f}s</span>", unsafe_allow_html=True)
            st.markdown(analisis_llm)
            texto_acumulado_respuesta += f"**🤖 Análisis LLM:**\n{analisis_llm}\n\n"
        else:
            st.markdown("#### Opinión del Experto")
            st.warning("Falta API Key")

    # Tab 3: Graphviz (capturamos el código para el historial)
    with tab3:
        if api_key:
            start_time_diag = time.perf_counter()
            with st.spinner("Generando diagrama..."):
                codigo_dot = generar_diagrama_dot(api_key, codigo_a_analizar)
            end_time_diag = time.perf_counter()
            diagram_time = end_time_diag - start_time_diag

            st.markdown(f"#### Diagrama de Seguimiento <span class='badge' style='color: var(--muted);'>Tiempo: {diagram_time:.2f}s</span>", unsafe_allow_html=True)
            
            if codigo_dot and ("digraph" in codigo_dot or "graph" in codigo_dot):
                try:
                    st.graphviz_chart(codigo_dot)
                    codigo_dot_para_historial = codigo_dot 
                    with st.expander("Ver código DOT"):
                        st.code(codigo_dot, language="dot")
                    texto_acumulado_respuesta += "**🕸️ Diagrama generado correctamente.**"
                except Exception as e:
                    st.error(f"Error visual: {e}")
            else:
                st.error("No se pudo generar diagrama válido.")
        else:
            st.markdown("#### Diagrama de Seguimiento")
            st.warning("Se requiere API Key")

    # ---------------------------
    # GUARDADO ESTRUCTURADO EN HISTORIAL
    # ---------------------------
    # Guardamos un DICCIONARIO
    mensaje_final_struct = {
        "text": texto_acumulado_respuesta,
        "dot_code": codigo_dot_para_historial
    }
    
    st.session_state.messages.append({"role": "assistant", "content": mensaje_final_struct})