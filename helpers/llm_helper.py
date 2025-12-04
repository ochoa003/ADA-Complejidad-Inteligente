# llm_helper.py

import streamlit as st
import google.generativeai as genai
import requests
import re
import os
import time
from dotenv import load_dotenv

# Importa los ejemplos como contexto desde data/pruebas.py
try:
    from data.pruebas import all_tests_code
except Exception:
    all_tests_code = ""  # Fallback si no está disponible

print(all_tests_code)

# Cargar variables de entorno desde .env
load_dotenv()

# Variable global para almacenar las reglas gramaticales
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

# Ejemplos de referencia del analizador (texto largo)
EJEMPLOS_PSEUDOCODIGO = all_tests_code

# Sistema: construir prompt fijo con TODOS los ejemplos optimizados
def build_system_prompt(incluir_ejemplos_completos=True):
    """
    Construye el prompt de sistema con todos los ejemplos.
    Optimiza el formato para reducir tokens sin perder información.
    """
    if not incluir_ejemplos_completos:
        ejemplos = "Ver ejemplos en contexto de la conversación."
    else:
        # COMPRIMIR ejemplos: quitar líneas vacías, comentarios verbose
        ejemplos_raw = all_tests_code or ""
        # Quitar múltiples saltos de línea consecutivos
        ejemplos = re.sub(r'\n\s*\n+', '\n', ejemplos_raw)
        # Quitar comentarios muy largos (mantener solo ►)
        ejemplos = re.sub(r'#[^\n]{100,}', '', ejemplos)
        # Limitar a ~20KB de ejemplos (aprox 5000 tokens)
        if len(ejemplos) > 20000:
            ejemplos = ejemplos[:20000] + "\n# ... (ejemplos adicionales truncados)"
    
    return f"""[SYSTEM]
Experto en ADA. RESPETA la gramática de los ejemplos.

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

def configurar_llm():
    """
    Configura y devuelve la API Key de Gemini desde variables de entorno.
    """
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ No se encontró GOOGLE_API_KEY en las variables de entorno")
            st.info("💡 Asegúrate de tener un archivo .env con GOOGLE_API_KEY configurado")
            return None
        genai.configure(api_key=api_key)
        return api_key
    except Exception as e:
        st.error(f"❌ Error al configurar la API: {e}")
        return None
# Modelos válidos (REST)
# Se prioriza la versión 1.5 por estabilidad, luego la 2.5 experimental
MODEL_CONFIGS = [
    ('v1beta', 'gemini-1.5-pro'),
    # ('v1beta', 'gemini-1.5-flash'),
    ('v1beta', 'gemini-2.5-flash'),
]

def _post(url, headers, data, retries=3):
    """POST con reintentos exponenciales ante 429/5xx."""
    delay = 1.0
    for intento in range(retries):
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        if resp.status_code in (429, 500, 502, 503, 504) and intento < retries - 1:
            time.sleep(delay)
            delay = min(delay * 2, 8.0)
            continue
        return resp
    return resp

def _build_payload(system_prompt: str, user_text: str, max_tokens=1024, stop_sequences=None, temperature=0.1, api_version='v1beta'):
    """
    Construye payload. Si system_prompt es muy grande (>30KB), 
    lo divide entre systemInstruction y el primer mensaje user.
    """
    # Límite de systemInstruction: ~30KB (seguro para v1beta)
    MAX_SYSTEM_SIZE = 30000
    
    if api_version == 'v1beta':
        if len(system_prompt) > MAX_SYSTEM_SIZE:
            # ESTRATEGIA: Dividir en dos partes
            # Parte 1: Gramática + reglas en systemInstruction
            # Parte 2: Ejemplos completos en primer mensaje del user
            
            # Extraer secciones
            gramatica_match = re.search(r'\[GRAMÁTICA\](.*?)\[EJEMPLOS', system_prompt, re.DOTALL)
            ejemplos_match = re.search(r'\[EJEMPLOS COMPLETOS\](.*?)\[REGLAS\]', system_prompt, re.DOTALL)
            reglas_match = re.search(r'\[REGLAS\](.*)', system_prompt, re.DOTALL)
            
            system_core = f"""[SYSTEM]
Experto en ADA. RESPETA la gramática de los ejemplos.

{gramatica_match.group(1) if gramatica_match else GRAMATICA_PROYECTO}

{reglas_match.group(1) if reglas_match else ""}
"""
            
            ejemplos_text = ejemplos_match.group(1) if ejemplos_match else ""
            
            # Combinar ejemplos con la tarea del usuario
            combined_user_text = f"""[CONTEXTO - EJEMPLOS DE REFERENCIA]
{ejemplos_text.strip()}

---
{user_text}"""
            
            return {
                "systemInstruction": { "parts": [ { "text": system_core.strip() } ] },
                "contents": [
                    { "role": "user", "parts": [ { "text": combined_user_text } ] }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "topP": 0.8,
                    "topK": 40,
                    "candidateCount": 1,
                    "maxOutputTokens": max_tokens,
                    "stopSequences": stop_sequences or []
                }
            }
        else:
            # System prompt cabe completo en systemInstruction
            return {
                "systemInstruction": { "parts": [ { "text": system_prompt } ] },
                "contents": [
                    { "role": "user", "parts": [ { "text": user_text } ] }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "topP": 0.8,
                    "topK": 40,
                    "candidateCount": 1,
                    "maxOutputTokens": max_tokens,
                    "stopSequences": stop_sequences or []
                }
            }
    else:  # v1
        # v1 no soporta systemInstruction, todo va en user
        combined_prompt = f"{system_prompt}\n\n---\n{user_text}"
        return {
            "contents": [
                { "role": "user", "parts": [ { "text": combined_prompt } ] }
            ],
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.8,
                "topK": 40,
                "candidateCount": 1,
                "maxOutputTokens": max_tokens,
                "stopSequences": stop_sequences or []
            }
        }

def traducir_a_pseudocodigo(api_key, texto_natural):
    """
    Traduce lenguaje natural a pseudocódigo con TODOS los ejemplos como contexto.
    """
    if api_key is None:
        return "❌ **Error:** La API Key no está configurada."

    errores = []
    
    # PROMPT DIRECTO - los ejemplos ya están en system/context
    user_prompt = f"""Convierte a pseudocódigo siguiendo EXACTAMENTE los patrones de los ejemplos.

Descripción: {texto_natural}

Devuelve SOLO:
begin
    ...
end"""

    for api_version, model_name in MODEL_CONFIGS:
        try:
            url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            
            # Payload con chunking automático de ejemplos
            data = _build_payload(
                SYSTEM_PROMPT,
                user_prompt,
                max_tokens=512,
                stop_sequences=None,
                temperature=0.0,
                api_version=api_version
            )
            
            # Safety settings
            if api_version == 'v1beta':
                data["safetySettings"] = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            
            response = _post(url, headers, data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Validación robusta
                if 'candidates' not in result or len(result['candidates']) == 0:
                    errores.append(f"❌ {model_name}: Sin candidatos")
                    continue
                
                candidate = result['candidates'][0]
                finish_reason = candidate.get('finishReason', 'UNKNOWN')
                
                if finish_reason == 'SAFETY':
                    errores.append(f"❌ {model_name}: Bloqueado por safety")
                    continue
                
                if 'content' not in candidate:
                    errores.append(f"❌ {model_name}: Sin 'content' (finishReason: {finish_reason})")
                    continue
                
                content = candidate['content']
                
                if 'parts' not in content or len(content['parts']) == 0:
                    errores.append(f"❌ {model_name}: Sin 'parts' en content")
                    continue
                
                texto_respuesta = content['parts'][0].get('text', '')
                
                if not texto_respuesta or len(texto_respuesta.strip()) < 5:
                    errores.append(f"❌ {model_name}: Respuesta vacía")
                    continue
                
                st.success(f"✅ Traducción con {model_name} (contexto completo)")
                limpio = limpiar_respuesta_llm(texto_respuesta)

                # Validación y corrección
                if not re.search(r'^\s*begin\s*$', limpio, re.MULTILINE) or not re.search(r'^\s*end\s*$', limpio, re.MULTILINE):
                    prompt_fix = f"""CORRIGE para cumplir gramática exacta de ejemplos.

Código:
{limpio}

Devuelve SOLO begin...end válido."""
                    
                    data_fix = _build_payload(SYSTEM_PROMPT, prompt_fix, max_tokens=256, stop_sequences=None, temperature=0.0, api_version=api_version)
                    if api_version == 'v1beta':
                        data_fix["safetySettings"] = data["safetySettings"]
                    
                    resp_fix = _post(url, headers, data_fix)
                    if resp_fix.status_code == 200:
                        result_fix = resp_fix.json()
                        if 'candidates' in result_fix and len(result_fix['candidates']) > 0:
                            cand = result_fix['candidates'][0]
                            if 'content' in cand and 'parts' in cand['content']:
                                fixed = cand['content']['parts'][0].get('text', '')
                                if fixed:
                                    return limpiar_respuesta_llm(fixed)
                
                return limpio
                
            elif response.status_code == 429:
                errores.append(f"❌ {model_name}: Cuota agotada")
                continue
            else:
                try:
                    error_msg = response.json().get('error', {}).get('message', response.text[:120])
                except:
                    error_msg = response.text[:120]
                errores.append(f"❌ {model_name}: HTTP {response.status_code} - {error_msg}")
                
        except Exception as e:
            errores.append(f"❌ {model_name}: {str(e)[:100]}")
            continue

    mensaje_error = "❌ **No se pudo traducir el texto.**\n\n"
    mensaje_error += "**Intentos:**\n" + "\n".join(f"- {e}" for e in errores)
    mensaje_error += "\n\n💡 Verifica cuota: https://aistudio.google.com"
    return mensaje_error

def limpiar_respuesta_llm(texto):
    """
    Limpia el bloque de código de la respuesta del LLM.
    Quita ```plaintext ... ``` o ``` ... ```
    Y aplica un post-procesado para forzar la gramática mínima.
    """
    match = re.search(r'```(?:plaintext\n)?(.*?)\n?```', texto, re.DOTALL)
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

def obtener_analisis_llm(api_key, pseudocodigo):
    """
    Envía el pseudocódigo a Gemini usando systemInstruction (v1beta) o prompt combinado (v1).
    """
    if api_key is None:
        return "❌ **Error:** La API Key no está configurada."

    errores = []
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

    for api_version, model_name in MODEL_CONFIGS:
        try:
            url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            data = _build_payload(
                SYSTEM_PROMPT,
                user_prompt,
                max_tokens=768,
                stop_sequences=["```", "FIN_RESPUESTA"],
                temperature=0.1,
                api_version=api_version
            )
            
            # AGREGAR SAFETY SETTINGS
            if api_version == 'v1beta':
                data["safetySettings"] = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            
            response = _post(url, headers, data)
            
            if response.status_code == 200:
                result = response.json()
                
                # VALIDACIÓN ROBUSTA
                if 'candidates' not in result or len(result['candidates']) == 0:
                    errores.append(f"❌ {model_name} ({api_version}): Sin candidatos")
                    continue
                
                candidate = result['candidates'][0]
                
                if candidate.get('finishReason') == 'SAFETY':
                    errores.append(f"❌ {model_name} ({api_version}): Bloqueado por seguridad")
                    continue
                
                if 'content' not in candidate or 'parts' not in candidate['content']:
                    errores.append(f"❌ {model_name} ({api_version}): Estructura de respuesta incompleta")
                    continue
                
                texto_respuesta = candidate['content']['parts'][0].get('text', '')
                
                if not texto_respuesta:
                    errores.append(f"❌ {model_name} ({api_version}): Respuesta vacía")
                    continue
                
                st.success(f"✅ Usando modelo: {model_name} ({api_version})")
                return texto_respuesta.strip()
                
            else:
                try:
                    error_detail = response.json().get('error', {}).get('message', response.text[:120])
                except:
                    error_detail = response.text[:120]
                errores.append(f"❌ {model_name} ({api_version}): HTTP {response.status_code} - {error_detail}")
                
        except KeyError as ke:
            errores.append(f"❌ {model_name} ({api_version}): Error de estructura - {str(ke)}")
            continue
        except Exception as e:
            errores.append(f"❌ {model_name} ({api_version}): {str(e)[:100]}")
            continue

    mensaje_error = "❌ **No se pudo conectar con ningún modelo de Gemini.**\n\n"
    mensaje_error += "**Intentos realizados:**\n" + "\n".join(f"- {e}" for e in errores)
    mensaje_error += "\n\n💡 **Soluciones:**\n- Verifica tu API Key en https://aistudio.google.com/apikey\n- Revisa cuotas y límites de rate en tu proyecto"
    return mensaje_error

def generar_diagrama_dot(api_key, pseudocodigo):
    """
    Solicita a Gemini que genere un código Graphviz (DOT) para visualizar el algoritmo.
    Detecta si es recursivo para sugerir un árbol, o iterativo para un diagrama de flujo.
    """
    if api_key is None:
        return None

    tipo_diagrama = "Diagrama de Flujo"
    if "CALL" in pseudocodigo and "algoritmo" in pseudocodigo: # Detección simple de recursividad
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

Usa formas estándar: Diamantes para condiciones (if/while), Rectángulos para procesos, Óvalos para Inicio/Fin.

Si es un árbol de recursión, muestra la jerarquía de llamadas.

NO incluyas explicaciones, SOLO el código DOT dentro de un bloque de código.

Usa etiquetas claras en las flechas (Sí/No, True/False).

Haz que el gráfico sea vertical (rankdir=TB). """

    configuraciones = [('v1beta', 'gemini-1.5-pro'),('v1beta', 'gemini-2.5-flash'), ('v1', 'gemini-2.5-flash'), ('v1beta', 'gemini-2.0-flash-exp'), ('v1beta', 'gemini-1.5-flash'), ('v1', 'gemini-1.5-pro'), ]

    for api_version, model_name in configuraciones:
        try:
            url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={api_key}"
            
            headers = {'Content-Type': 'application/json'}
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt_diagrama
                    }]
                }]
            }
    
        
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                texto_respuesta = result['candidates'][0]['content']['parts'][0]['text']

                # Limpiamos el resultado para obtener solo el código DOT
                # Buscamos contenido entre ```dot ... ``` o simplemente el texto si no tiene tags
                match = re.search(r'```(?:dot|graphviz)?\n?(.*?)```', texto_respuesta, re.DOTALL)
                if match:
                    return match.group(1).strip()
                return texto_respuesta.strip()

        except Exception:
            continue