# ADA: Complejidad inteligente

Analizador de complejidad algorítmica a partir de pseudocódigo estructurado. Combina análisis estático local con apoyo de un LLM para:
- Traducir descripciones en lenguaje natural a pseudocódigo.
- Dar una segunda opinión de complejidad.
- Generar diagramas de flujo (DOT/Graphviz).
- Medir tiempos de respuesta del analizador y del LLM en segundos.

## Características
- Soporta algoritmos iterativos y recursivos.
- Estima O, Ω, Θ con composición de costos por bloques y bucles.
- Heurísticas para while/repeat (lineal/log), if/else (peor/mejor), y DP básica (tablas 1D/2D, memoización).
- Opinión del LLM y diagrama DOT opcionales (requiere API key).
- UI en Streamlit con tres pestañas: Análisis, Opinión LLM y Diagrama.
- Latencias mostradas en segundos para: Traducción, Análisis local, LLM y Diagrama.

## Estructuras de pseudocódigo soportadas
- Bloques: begin / end
- Bucles: 
  - for i 🡨 inicio to fin do
  - while (condición) do
  - repeat … until (condición)
- Condicionales: if (condición) then, else
- Asignaciones y retorno: x 🡨 expr, return expr
- Llamadas: CALL nombre_funcion(args)
- Arreglos: A[i], A[i][j], length(A)
- Pistas opcionales: ► O(n), ► O(n^2), ► O(log n)
- Declaraciones simples: tipo var, var[], etc.

## Arquitectura
- models/analizador.py: núcleo del análisis estático (iterativo/recursivo, DP, Teorema Maestro/heurística BnB).
- views/UI.py: interfaz Streamlit, orquestación, medición de tiempos, render de resultados.
- helpers/llm_helper.py: integración con LLM (traducción, segunda opinión, DOT).
- data/pruebas.py: ejemplos de pseudocódigo para pruebas rápidas.

## Requisitos
- Python 3.10+
- Paquetes Python:
  - streamlit
  - google-generativeai (para LLM Gemini)
  - graphviz (paquete Python)

Instalación rápida (PowerShell):
```powershell
cd c:\Users\dand1\OneDrive\Escritorio\ADA
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install streamlit google-generativeai graphviz
```

Configurar API Key (Gemini):
```powershell
setx GOOGLE_API_KEY "tu_api_key_de_gemini"
# Cierra y reabre la terminal para que surta efecto
```

## Ejecución
```powershell
cd c:\Users\dand1\OneDrive\Escritorio\ADA
.\.venv\Scripts\Activate.ps1
streamlit run views\UI.py
```

## Uso
1) Escribe pseudocódigo begin/end o activa “Entrada en lenguaje natural” para traducir.
2) Pulsa “Analizar”.
3) Revisa:
   - Pestaña “📊 Análisis”: O/Ω/Θ calculadas localmente y Tiempo (s) del analizador.
   - Pestaña “🤖 Opinión del LLM”: segunda opinión y Tiempo (s) del LLM.
   - Pestaña “🕸️ Diagrama”: gráfico y Tiempo (s) de generación.

Ejemplo mínimo:
```plaintext
begin
  for i 🡨 1 to n do
  begin
    x 🡨 x + 1
  end
end
```

Salida (ejemplo):
- Peor Caso (O): O(n)
- Mejor Caso (Ω): Ω(n)
- Caso Promedio (Θ): Θ(n)

## Evaluación empírica
- Complejidad del analizador: Θ(C) respecto al tamaño del texto (caracteres).
- Se observaron latencias lineales al crecer C.
- La UI muestra tiempos en segundos: análisis local, LLM y diagrama.

## Licencia
Este proyecto se publica con fines educativos. Ajusta la licencia según tus necesidades.

## Resumen
- Análisis estático: models/analizador.py
- Interfaz: Streamlit
- LLM: Google Generative AI (Gemini) para traducción, opinión y diagramas DOT

## Autores
- Esteban Ochoa Silva
- Jhonatan David Gómez Castaño