# llm_helper.py (Groq)
# Mantiene la misma interfaz pública que la versión de Gemini:
# - configurar_llm()
# - traducir_a_pseudocodigo(api_key, texto_natural)
# - obtener_analisis_llm(api_key, pseudocodigo)
# - generar_diagrama_dot(api_key, pseudocodigo)
#
# Internamente usa la API de Groq (Chat Completions) vía requests.

import streamlit as st
import requests
import re
import os
import time
from dotenv import load_dotenv

# Contexto opcional de ejemplos
try:
    from data.pruebas import all_tests_code
except Exception:
    all_tests_code = ""

# Cargar variables de entorno
load_dotenv()

# Gramática del proyecto (se mantiene igual)
GRAMATICA_PROYECTO = """
- Las asignaciones usan '🡨'. Ejemplo: x 🡨 10
- Los bucles son: 'for ... to ... do', 'while ... do', 'repeat ... until'
- Los condicionales son 'if (...) then' con 'else' opcional
- Los comentarios usan '►'
- Las llamadas a subrutinas usan 'CALL nombre(parametros)'
- El acceso a arreglos es A[i] y el tamaño es length(A)
- Todo bloque de código debe estar entre 'begin' y 'end'
- Las declaraciones de variables van ANTES del 'begin'
"""

EJEMPLOS_PSEUDOCODIGO = all_tests_code

def build_system_prompt(incluir_ejemplos_completos=True):
    """Construye prompt de sistema con gramática y ejemplos (compactado)."""
    if not incluir_ejemplos_completos:
        ejemplos = "Ver ejemplos en contexto de la conversación."
    else:
        ejemplos_raw = EJEMPLOS_PSEUDOCODIGO or ""
        ejemplos = re.sub(r'\n\s*\n+', '\n', ejemplos_raw)
        ejemplos = re.sub(r'#[^\n]{100,}', '', ejemplos)
        if len(ejemplos) > 20000:
            ejemplos = ejemplos[:20000] + "\n# ... (ejemplos adicionales truncados)"
    return f"""[SYSTEM]
Eres experto en ADA y debes RESPETAR la gramática especificada.

[GRAMÁTICA]
{GRAMATICA_PROYECTO}

[EJEMPLOS COMPLETOS]
{ejemplos}

[REGLAS]
- Traducción: SOLO begin...end
- Análisis: Markdown con O/Ω/Θ
- NO cambies símbolos (🡨, ►, etc.)
"""

SYSTEM_PROMPT = build_system_prompt(incluir_ejemplos_completos=True)

# ------------------------------
# Configuración Groq
# ------------------------------
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Recomendado: "llama-3.1-70b-versatile" o "mixtral-8x7b-32768"
GROQ_MODEL_TRANSLATE = "llama-3.1-8b-instant"
GROQ_MODEL_ANALYZE = "llama-3.1-8b-instant"
GROQ_MODEL_DOT = "llama-3.1-8b-instant"

def configurar_llm():
    """
    Configura y devuelve la API Key de Groq desde variables de entorno.
    También acepta la clave directa si ya la tienes (ej: gsk_...).
    """
    try:
        # Si el usuario te pasó la key directamente, puedes setearla en .env como GROQ_API_KEY
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            # Mensaje más claro
            st.error("❌ No se encontró GROQ_API_KEY en variables de entorno")
            st.info("💡 Agrega GROQ_API_KEY al .env o al entorno del sistema")
            return None
        return api_key
    except Exception as e:
        st.error(f"❌ Error al configurar la API: {e}")
        return None

def _groq_chat(api_key: str, system_prompt: str, user_prompt: str, model: str, max_tokens: int = 1024, temperature: float = 0.2, retries: int = 3, timeout: int = 60):
    """
    Wrapper para llamar a Groq Chat Completions con reintentos simples ante 429/5xx.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    delay = 1.0
    for intento in range(retries):
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=timeout)
        if resp.status_code in (429, 500, 502, 503, 504) and intento < retries - 1:
            time.sleep(delay)
            delay = min(delay * 2, 8.0)
            continue
        return resp
    return resp

# ------------------------------
# Traducción a pseudocódigo
# ------------------------------
def traducir_a_pseudocodigo(api_key, texto_natural):
    """
    Traduce lenguaje natural a pseudocódigo siguiendo EXACTAMENTE la gramática.
    """
    if api_key is None:
        return "❌ **Error:** La API Key no está configurada."

    user_prompt = f"""Convierte a pseudocódigo siguiendo EXACTAMENTE los patrones de los ejemplos.

Descripción: {texto_natural}

Devuelve SOLO:
begin
    ...
end"""

    resp = _groq_chat(
        api_key=api_key,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=GROQ_MODEL_TRANSLATE,
        max_tokens=512,
        temperature=0.0
    )

    if resp.status_code == 200:
        data = resp.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except Exception:
            return "❌ Error: Respuesta inválida de Groq."
        limpio = limpiar_respuesta_llm(text)

        # Validación begin/end mínima; si falta, segunda pasada para corregir
        if not re.search(r'^\s*begin\s*$', limpio, re.MULTILINE) or not re.search(r'^\s*end\s*$', limpio, re.MULTILINE):
            prompt_fix = f"""CORRIGE para cumplir gramática exacta de ejemplos.

Código:
{limpio}

Devuelve SOLO begin...end válido."""
            resp_fix = _groq_chat(
                api_key=api_key,
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt_fix,
                model=GROQ_MODEL_TRANSLATE,
                max_tokens=256,
                temperature=0.0
            )
            if resp_fix.status_code == 200:
                data_fix = resp_fix.json()
                try:
                    fixed = data_fix["choices"][0]["message"]["content"]
                    if fixed:
                        return limpiar_respuesta_llm(fixed)
                except Exception:
                    pass
        st.success(f"✅ Traducción realizada con Groq ({GROQ_MODEL_TRANSLATE})")
        return limpio

    else:
        try:
            err = resp.json()
            msg = err.get("error", {}).get("message", str(err))
        except Exception:
            msg = resp.text
        return f"❌ Error HTTP {resp.status_code}: {msg[:200]}"

def limpiar_respuesta_llm(texto: str):
    """
    Limpia el bloque de código de la respuesta.
    Quita ```plaintext ... ``` o ``` ... ```
    Filtra líneas que cumplen la gramática y garantiza begin/end.
    """
    match = re.search(r'```(?:plaintext|text)?\n?(.*?)\n?```', texto, re.DOTALL)
    if match:
        texto = match.group(1).strip()

    lineas = []
    for linea in texto.splitlines():
        s = linea.strip()
        if s in ("begin", "end") or \
           re.match(r'^(for|while|repeat|until|if|else|return|CALL)\b', s, re.IGNORECASE) or \
           re.search(r'🡨', s) or \
           re.search(r'\blength\(\w+\)\b', s) or \
           re.search(r'\w+\s*\[\s*\w+\s*\]', s) or \
           s.startswith("►"):
            lineas.append(linea)

    joined = "\n".join(lineas).strip()
    if "begin" not in joined or "end" not in joined:
        joined = "begin\n" + "\n".join(lineas) + "\nend"
    return joined.strip()

# ------------------------------
# Segunda opinión (análisis LLM)
# ------------------------------
def obtener_analisis_llm(api_key, pseudocodigo):
    """
    Envía el pseudocódigo a Groq y devuelve un análisis breve con O/Ω/Θ.
    """
    if api_key is None:
        return "❌ **Error:** La API Key no está configurada."

    user_prompt = f"""[TAREA]
Analiza el siguiente algoritmo y devuelve:
1) Razonamiento breve
2) Complejidad: Peor Caso (O), Mejor Caso (Ω) y Caso Promedio (Θ).

[PSEUDOCÓDIGO]
```plaintext
{pseudocodigo}
```

[OUTPUT]
- En Markdown, conciso.
- No incluyas texto fuera del análisis.
"""

    resp = _groq_chat(
        api_key=api_key,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=GROQ_MODEL_ANALYZE,
        max_tokens=768,
        temperature=0.1
    )

    if resp.status_code == 200:
        try:
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            st.success(f"✅ Usando Groq: {GROQ_MODEL_ANALYZE}")
            return text.strip()
        except Exception:
            return "❌ Error: Estructura de respuesta inválida de Groq."
    else:
        try:
            err = resp.json()
            msg = err.get("error", {}).get("message", str(err))
        except Exception:
            msg = resp.text
        return f"❌ Error HTTP {resp.status_code}: {msg[:200]}"

# ------------------------------
# Diagrama DOT (Graphviz)
# ------------------------------
def generar_diagrama_dot(api_key, pseudocodigo):
    """
    Solicita al LLM Groq un código DOT para visualizar el algoritmo.
    Si detecta recursividad simple, sugiere árbol de llamadas; si no, flujo.
    """
    if api_key is None:
        return None

    tipo_diagrama = "Diagrama de Flujo"
    if "CALL" in pseudocodigo and "algoritmo" in pseudocodigo:
        tipo_diagrama = "Árbol de Recursión (mostrando las ramas de llamadas)"

    prompt_diagrama = f"""
**Rol:** Eres un experto en visualización de algoritmos.

**Tarea:** Genera el código fuente en lenguaje DOT (Graphviz) para representar el siguiente pseudocódigo.
El tipo de representación debe ser: **{tipo_diagrama}**.

**Pseudocódigo:**
```plaintext
{pseudocodigo}
```
Requisitos del DOT:
- rankdir=TB (vertical)
- Diamantes para condiciones (if/while), Rectángulos para procesos, Óvalos para Inicio/Fin.
- Si es un árbol de recursión, muestra la jerarquía de llamadas.
- NO incluyas explicaciones, SOLO el código DOT dentro de un bloque de código.
- Usa etiquetas claras en las flechas (Sí/No, True/False).
"""

    resp = _groq_chat(
        api_key=api_key,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt_diagrama,
        model=GROQ_MODEL_DOT,
        max_tokens=512,
        temperature=0.2
    )

    if resp.status_code == 200:
        try:
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            # Intentar extraer solo el bloque DOT
            match = re.search(r'```(?:dot|graphviz)?\n?(.*?)```', text, re.DOTALL)
            if match:
                return match.group(1).strip()
            return text.strip()
        except Exception:
            return None
    else:
        return None