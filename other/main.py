import re

def analizar_complejidad(pseudocodigo):
    """
    Analiza un pseudocódigo simple para determinar su complejidad Big O.
    Soporta:
    - Asignaciones (costo O(1))
    - Bucles FOR simples (for i <- 1 to n)
    - Bucles FOR anidados.
    """
    lineas = pseudocodigo.strip().split('\n')
    costo_total = 0
    multiplicadores_bucle = [] # Pila para manejar bucles anidados

    print("--- Inicio del Análisis Línea por Línea ---")

    for i, linea in enumerate(lineas):
        linea = linea.strip()
        
        # Ignorar comentarios y líneas vacías
        if not linea or linea.startswith('►'):
            print(f"Línea {i+1}: '{linea}' -> Ignorada (Comentario o vacía)")
            continue

        # Detectar inicio de un bucle FOR
        # Usamos una expresión regular para capturar "n"
        match_for = re.search(r'for\s+\w+\s*🡨\s*\d+\s+to\s+(\w+)\s+do', linea)
        if match_for:
            limite_bucle = match_for.group(1)
            multiplicadores_bucle.append(limite_bucle)
            print(f"Línea {i+1}: '{linea}' -> Inicio de bucle FOR. Límite: {limite_bucle}. Profundidad actual: {len(multiplicadores_bucle)}")
            continue

        # Detectar fin de bloque 'end'
        if linea == 'end':
            if multiplicadores_bucle:
                terminado = multiplicadores_bucle.pop()
                print(f"Línea {i+1}: '{linea}' -> Fin de bucle con límite '{terminado}'. Profundidad actual: {len(multiplicadores_bucle)}")
            else:
                 print(f"Línea {i+1}: '{linea}' -> 'end' sin un 'for' correspondiente. Se ignora.")
            continue
            
        # Considerar cualquier otra instrucción como una asignación o acción de costo constante O(1)
        if '🡨' in linea or 'call' in linea.lower() or linea not in ['begin', 'repeat', 'until', 'if', 'else', 'while']:
            costo_instruccion = 1
            
            # Si la instrucción está dentro de un bucle, su costo se multiplica
            costo_calculado = f"{costo_instruccion}"
            if multiplicadores_bucle:
                factores = " * ".join(multiplicadores_bucle)
                costo_calculado = f"{costo_instruccion} * {factores}"
                # Aquí se suma simbólicamente, la expresión final se construye al final
            
            # Para el cálculo real, necesitamos una expresión simbólica
            if not multiplicadores_bucle:
                 costo_total += 1
            
            print(f"Línea {i+1}: '{linea}' -> Instrucción de costo constante. Costo acumulado: {costo_calculado}")


    # Construir la expresión de complejidad final
    # Este es un enfoque simplificado para el peor caso (Big O)
    variables_complejidad = set()
    for linea in lineas:
        match_for = re.search(r'for\s+\w+\s*🡨\s*\d+\s+to\s+(\w+)\s+do', linea)
        if match_for:
            variables_complejidad.add(match_for.group(1))
    
    # Determinar el orden de complejidad basado en la anidación máxima
    max_anidacion = 0
    anidacion_actual = 0
    for linea in lineas:
        if 'for' in linea:
            anidacion_actual += 1
            max_anidacion = max(max_anidacion, anidacion_actual)
        if 'end' in linea and anidacion_actual > 0:
            anidacion_actual -= 1
            
    if max_anidacion == 0:
        complejidad = "O(1)"
    elif max_anidacion == 1:
        # Asume que la variable del bucle principal es la dominante
        var_dominante = next(iter(variables_complejidad), 'n')
        complejidad = f"O({var_dominante})"
    else:
        var_dominante = next(iter(variables_complejidad), 'n')
        complejidad = f"O({var_dominante}^{max_anidacion})"

    print("\n--- Resultado Final ---")
    return complejidad


# --- Conjunto de Pruebas (Entregable) ---

# Prueba 1: Algoritmo Lineal
algo_lineal = """
begin
    suma 🡨 0 ► Costo 1
    for i 🡨 1 to n do
    begin
        suma 🡨 suma + A[i] ► Se ejecuta n veces
    end
    CALL print(suma) ► Costo 1
end
"""

# Prueba 2: Algoritmo Cuadrático (Bucle anidado)
algo_cuadratico = """
begin
    suma 🡨 0
    for i 🡨 1 to n do
    begin
        for j 🡨 1 to n do
        begin
            suma 🡨 suma + 1 ► Se ejecuta n*n veces
        end
    end
end
"""

# Prueba 3: Algoritmo Constante
algo_constante = """
begin
    x 🡨 10
    y 🡨 20
    z 🡨 x + y
    CALL print(z)
end
"""

print("Análisis del Algoritmo Lineal:")
print(f"Complejidad calculada: {analizar_complejidad(algo_lineal)}\n")

print("Análisis del Algoritmo Cuadrático:")
print(f"Complejidad calculada: {analizar_complejidad(algo_cuadratico)}\n")

print("Análisis del Algoritmo Constante:")
print(f"Complejidad calculada: {analizar_complejidad(algo_constante)}\n")