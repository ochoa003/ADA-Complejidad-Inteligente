
from models.analizador import analizar_complejidad

# Prueba 1: Algoritmo Constante
algo_constante = """
begin
    x 🡨 10
    y 🡨 20
    z 🡨 x + y
end
"""

# Prueba 2: Algoritmo Lineal (FOR)
algo_lineal = """
begin
    suma 🡨 0
    for i 🡨 1 to n do
    begin
        suma 🡨 suma + 1
    end
end
"""

# Prueba 3: Algoritmo Cuadrático (FOR anidado)
algo_cuadratico = """
begin
    suma 🡨 0
    for i 🡨 1 to n do
    begin
        for j 🡨 1 to n do
        begin
            suma 🡨 suma + 1
        end
    end
end
"""

# Prueba 4: Algoritmo con Condicional (Mejor y Peor Caso)
algo_condicional = """
begin
    if (condicion_externa) then
    begin
        for i 🡨 1 to n do
        begin
            x 🡨 x + 1
        end
    end
    else
    begin
        y 🡨 10
    end
end
"""

# Prueba 5: Bucle WHILE con patrón lineal
algo_while_lineal = """
begin
    i 🡨 0
    while (i < n) do
    begin
        x 🡨 x + 1
        i 🡨 i + 1
    end
end
"""

# Prueba 6: Bucle REPEAT con patrón logarítmico
algo_repeat_log = """
begin
    i 🡨 1
    repeat
        x 🡨 x * 2
        i 🡨 i * 2
    until (i ≥ n)
end
"""

# Prueba 7: Búsqueda Binaria Recursiva
# T(n) = 1T(n/2) + O(1) -> a=1, b=2, f(n)=1. log2(1) = 0. Caso 2 -> O(log n)
algo_busqueda_binaria = """
algoritmo(A, n)
begin
    ► Trabajo constante
    x 🡨 1 
    y 🡨 2
    if (condicion_base) then
        return encontrado
    end
    ► Llamada recursiva con la mitad de los datos
    CALL algoritmo(A, n/2)
end
"""

# Prueba 8: Merge Sort (simplificado)
# T(n) = 2T(n/2) + O(n) -> a=2, b=2, f(n)=n. log2(2) = 1. Caso 2 -> O(n log n)
algo_merge_sort = """
algoritmo(A, n)
begin
    if (n < 2) then
        return
    end
    ► Dos llamadas recursivas con la mitad de los datos
    CALL algoritmo(A, n/2)
    CALL algoritmo(A, n/2)
    ► Trabajo lineal para combinar los resultados
    for i 🡨 1 to n do
        begin
            combinar(A, i)
        end
end
"""

# Prueba 9: Búsqueda lineal en un arreglo
# El bucle se ejecuta 'length(A)' veces, lo que equivale a O(n)
algo_busqueda_arreglo = """
begin
    encontrado 🡨 F
    for i 🡨 1 to length(A) do
    begin
        if (A[i] = valor_buscado) then
            encontrado 🡨 T
        end
    end
end
"""

# Prueba 10: Declaraciones de Variables y Arreglos (debe seguir siendo O(1))
algo_con_declaraciones = """
Casa mi_casa 
datos[10]     
i            

begin
    x 🡨 10
    mi_casa.Area 🡨 100
    datos[1] 🡨 5
end
"""

# Prueba 11: Algoritmo Lineal con Declaraciones (debe seguir siendo O(n))
algo_lineal_con_declaraciones = """
vector_a[n]
vector_b[n]
i

begin
    for i 🡨 1 to n do
    begin
        vector_b[i] 🡨 vector_a[i] + 1
    end
end
"""

# Prueba 12: Bucle lineal con llamada a función O(1)
algo_call_o1 = """
begin
    for i 🡨 1 to n do
    begin
        CALL imprimir(i)  ► O(1)
    end
end
"""
# Esperado: O(n)

# Prueba 13: Bucle lineal con llamada a función O(n)
# Nota: La complejidad se convierte en O(n^2)
algo_call_on = """
begin
    for i 🡨 1 to n do
    begin
        CALL busqueda_lineal(A, n)  ► O(n)
    end
end
"""
# Esperado: O(n^2)

# Prueba 14: Bucle O(n^2) con llamada O(1)
algo_call_anidado = """
begin
    for i 🡨 1 to n do
    begin
        for j 🡨 1 to n do
        begin
            CALL swap(A, i, j)  ► O(1)
        end
    end
end
"""
# Esperado: O(n^2)

# Prueba 15: Función recursiva que llama a una O(n)
# T(n) = 2T(n/2) + O(n). f(n) ahora incluye una llamada a 'combinar' O(n)
algo_call_merge_sort_detallado = """
algoritmo(A, n)
begin
    if (n < 2) then
        return
    end
    CALL algoritmo(A, n/2)
    CALL algoritmo(A, n/2)
    CALL combinar(A, n) ► Trabajo extra O(n)
end
"""
# Esperado: O(n log n)


# Prueba 16: Bucle con límite polinomial (to n^2)
algo_for_n2 = """
begin
    suma 🡨 0
    for i 🡨 1 to n^2 do
    begin
        suma 🡨 suma + 1
    end
end
"""
# Esperado: O(n^2)

# Prueba 17: Triple bucle anidado
algo_cubico = """
begin
    c 🡨 0
    for i 🡨 1 to n do
    begin
        for j 🡨 1 to n do
        begin
            for k 🡨 1 to n do
            begin
                c 🡨 c + 1
            end
        end
    end
end
"""
# Esperado: O(n^3)

# Prueba 18: While halving (log n) con trabajo constante
algo_while_log = """
begin
    i 🡨 n
    while (i > 1) do
    begin
        x 🡨 x + 1
        i 🡨 i / 2
    end
end
"""
# Esperado: O(log n)

# Prueba 19: For n con trabajo log n dentro
algo_for_con_log_interno = """
begin
    for i 🡨 1 to n do
    begin
        j 🡨 1
        while (j < n) do
        begin
            j 🡨 j * 2
        end
    end
end
"""
# Esperado: O(n log n)

# Prueba 20: If-else con ramas equilibradas
algo_if_balanceado = """
begin
    if (cond) then
    begin
        for i 🡨 1 to n do
        begin
            x 🡨 x + 1
        end
    end
    else
    begin
        for j 🡨 1 to n do
        begin
            y 🡨 y + 1
        end
    end
end
"""
# Esperado: Peor O(n), Mejor Ω(n), Promedio Θ(n)

# Prueba 21: Acceso a arreglo en for
algo_for_length_m = """
begin
    for i 🡨 1 to length(B) do
    begin
        x 🡨 B[i]
    end
end
"""
# Esperado: O(n) (asumiendo length(B) ~ n)

# Prueba 22: For con paso constante pero trabajo O(n) interno
algo_for_y_for_interno = """
begin
    for i 🡨 1 to n do
    begin
        for j 🡨 1 to n do
        begin
            x 🡨 x + 1
        end
    end
end
"""
# Esperado: O(n^2)

# Prueba 23: Repeat con multiplicación por 3 (log n)
algo_repeat_log_base3 = """
begin
    k 🡨 1
    repeat
        k 🡨 k * 3
    until (k ≥ n)
end
"""
# Esperado: O(log n)

# Prueba 24: While lineal con condición basada en length(A)
algo_while_length = """
begin
    i 🡨 0
    while (i < length(A)) do
    begin
        i 🡨 i + 1
    end
end
"""
# Esperado: O(n)

# Prueba 25: Llamada conocida en bucle cuadrático
algo_call_swap_n2 = """
begin
    for i 🡨 1 to n do
    begin
        for j 🡨 1 to n do
        begin
            CALL swap(A, i, j)
        end
    end
end
"""
# Esperado: O(n^2)

# Prueba 26: Llamada O(n) en bucle O(n log n) interno
algo_mixto_call_y_log = """
begin
    for i 🡨 1 to n do
    begin
        CALL busqueda_lineal(A, n)  ► O(n)
        k 🡨 1
        while (k < n) do
        begin
            k 🡨 k * 2
        end
    end
end
"""
# Esperado: O(n * (n + log n)) → O(n^2)

# Prueba 27: If con rama pesada n^2 y rama ligera constante
algo_if_pesado = """
begin
    if (cond) then
    begin
        for i 🡨 1 to n do
        begin
            for j 🡨 1 to n do
            begin
                x 🡨 x + 1
            end
        end
    end
    else
    begin
        x 🡨 1
    end
end
"""
# Esperado: Peor O(n^2), Mejor Ω(1)

# Prueba 28: For hasta m (otro parámetro), trabajo constante
algo_for_m = """
begin
    for i 🡨 1 to m do
    begin
        x 🡨 x + 1
    end
end
"""
# Esperado: O(m) (si m ≠ n)

# Prueba 29: Combinación n y m en doble bucle
algo_for_n_y_m = """
begin
    for i 🡨 1 to n do
    begin
        for j 🡨 1 to m do
        begin
            x 🡨 x + 1
        end
    end
end
"""
# Esperado: O(n*m)

# Prueba 30: Recursión con 3 llamadas y trabajo lineal
# T(n) = 3T(n/2) + O(n) → a=3, b=2, f(n)=n; log_2(3) ≈ 1.585 > 1 → O(n^{log_2 3})
algo_recursion_3_llamadas = """
algoritmo(A, n)
begin
    if (n < 2) then
        return
    end
    CALL algoritmo(A, n/2)
    CALL algoritmo(A, n/2)
    CALL algoritmo(A, n/2)
    for i 🡨 1 to n do
    begin
        x 🡨 x + 1
    end
end
"""
# Esperado: O(n^{log_2 3})

# Prueba DP 1: Tabla 1D con bucle único (O(n))
algo_dp_1d = """
begin
    for i 🡨 1 to n do
    begin
        dp[i] 🡨 dp[i-1] + 1
    end
end
"""
# Esperado: O(n)

# Prueba DP 2: Tabla 2D con doble bucle (O(n*m))
algo_dp_2d = """
begin
    for i 🡨 1 to n do
    begin
        for j 🡨 1 to m do
        begin
            dp[i][j] 🡨 min(dp[i-1][j], dp[i][j-1]) + 1
        end
    end
end
"""
# Esperado: O(n*m)

# Prueba DP 3: Memoización 1D sin bucles (heurística O(n))
algo_dp_memo_1d = """
begin
    if (memo[i] != -1) then
        return memo[i]
    end
    memo[i] 🡨 1
end
"""
# Esperado: O(n) (heurístico por número de estados)

# Prueba DP 4: Memoización 2D sin bucles (heurística O(n*m))
algo_dp_memo_2d = """
begin
    if (memo[i][j] != -1) then
        return memo[i][j]
    end
    memo[i][j] 🡨 1
end
"""
# Esperado: O(n*m) (heurística por número de estados)

# Prueba DP 5: DP 2D con transición O(1) y for n^2 (O(n^2))
algo_dp_2d_n2 = """
begin
    for i 🡨 1 to n do
    begin
        for j 🡨 1 to n do
        begin
            dp[i][j] 🡨 max(dp[i-1][j], dp[i][j-1]) + 1
        end
    end
end
"""
# Esperado: O(n^2)

# Prueba DP 6: DP 1D con while log interno (O(n log n))
algo_dp_1d_log = """
begin
    for i 🡨 1 to n do
    begin
        j 🡨 1
        while (j < n) do
        begin
            j 🡨 j * 2
        end
        dp[i] 🡨 dp[i-1] + j
    end
end
"""
# Esperado: O(n log n)

# BnB 1: Subconjuntos con poda por cota (bound >= best)
algo_bnb_subsets = """
algoritmo(S, n, idx, cost, best, bound)
begin
    if (bound >= best) then
        return
    end
    if (idx = n) then
        if (cost < best) then
            best 🡨 cost
        end
        return
    end
    # Ramificar: tomar o no tomar
    CALL algoritmo(S, n, idx+1, cost, best, bound)
    CALL algoritmo(S, n, idx+1, cost + S[idx], best, bound)
end
"""
# Esperado: Peor O(2^n), Mejor Ω(n), Promedio entre Ω(n) y O(2^n)

# BnB 2: TSP con poda por lower bound
algo_bnb_tsp = """
algoritmo(G, n, nivel, cost, best, lower)
begin
    if (lower >= best) then
        return
    end
    if (nivel = n) then
        if (cost < best) then
            best 🡨 cost
        end
        return
    end
    for i 🡨 1 to n do
    begin
        CALL algoritmo(G, n, nivel+1, cost + 1, best, lower)
    end
end
"""
# Esperado: Peor O(n^n) ~ O(n!) aproximado, Mejor Ω(n), Promedio entre Ω(n) y O(n^n)

# BnB 3: Knapsack con poda y divide y vencerás n/2 (mezcla)
algo_bnb_knapsack = """
algoritmo(W, V, n, idx, cost, best, bound)
begin
    if (bound >= best) then
        return
    end
    if (idx >= n) then
        return
    end
    CALL algoritmo(W, V, n/2, idx+1, cost, best, bound)
    CALL algoritmo(W, V, n/2, idx+1, cost + V[idx], best, bound)
end
"""
# Esperado: Peor O(n^{log_2 2}) = O(n), Mejor Ω(n), (con poda) rango entre Ω(n) y O(n)





# --- Ejecución de todas las pruebas ---
print("="*40)
print("Prueba 1: Análisis del Algoritmo Constante")
print(analizar_complejidad(algo_constante)) # Esperado: O(1)
print("="*40)

print("\nPrueba 2: Análisis del Algoritmo Lineal (FOR)")
print(analizar_complejidad(algo_lineal)) # Esperado: O(n)
print("="*40)

print("\nPrueba 3: Análisis del Algoritmo Cuadrático")
print(analizar_complejidad(algo_cuadratico)) # Esperado: O(n^2)
print("="*40)

print("\nPrueba 4: Análisis del Algoritmo Condicional")
print(analizar_complejidad(algo_condicional)) # Esperado: Peor O(n), Mejor Ω(1)
print("="*40)

print("\nPrueba 5: Análisis del Bucle WHILE Lineal")
print(analizar_complejidad(algo_while_lineal)) # Esperado: O(n)
print("="*40)

print("\nPrueba 6: Análisis del Bucle REPEAT Logarítmico")
print(analizar_complejidad(algo_repeat_log)) # Esperado: O(log n)
print("="*40)

print("="*40)
print("Prueba 7: Análisis de Búsqueda Binaria Recursiva")
print(analizar_complejidad(algo_busqueda_binaria, nombre_funcion="algoritmo"))
print("="*40)

print("\nPrueba 8: Análisis de Merge Sort")
print(analizar_complejidad(algo_merge_sort, nombre_funcion="algoritmo"))
print("="*40)

print("="*40)
print("Prueba 9: Análisis de Búsqueda Lineal en Arreglo")
print(analizar_complejidad(algo_busqueda_arreglo))
print("="*40)

# --- Ejecución de las nuevas pruebas ---
print("="*40)
print("Prueba 10: Análisis con Declaraciones de Variables y Objetos")
print(analizar_complejidad(algo_con_declaraciones))
print("="*40)

print("\nPrueba 11: Análisis Lineal con Declaraciones")
print(analizar_complejidad(algo_lineal_con_declaraciones))
print("="*40)

print("="*40)
print("Prueba 12: Bucle Lineal con CALL O(1)")
print(analizar_complejidad(algo_call_o1))
print("="*40)

print("\nPrueba 13: Bucle Lineal con CALL O(n)")
print(analizar_complejidad(algo_call_on))
print("="*40)

print("\nPrueba 14: Bucle O(n^2) con CALL O(1)")
print(analizar_complejidad(algo_call_anidado))
print("="*40)

print("\nPrueba 15: Recursivo con CALL O(n) en f(n)")
print(analizar_complejidad(algo_call_merge_sort_detallado, nombre_funcion="algoritmo"))
print("="*40)



# --- Ejecución de las pruebas 16–30 ---
print("="*40)
print("Prueba 16: For con límite n^2")
print(analizar_complejidad(algo_for_n2))
print("="*40)

print("Prueba 17: Triple bucle anidado")
print(analizar_complejidad(algo_cubico))
print("="*40)

print("Prueba 18: While halving (log n)")
print(analizar_complejidad(algo_while_log))
print("="*40)

print("Prueba 19: For con log interno")
print(analizar_complejidad(algo_for_con_log_interno))
print("="*40)

print("Prueba 20: If-else equilibrado")
print(analizar_complejidad(algo_if_balanceado))
print("="*40)

print("Prueba 21: For sobre length(B)")
print(analizar_complejidad(algo_for_length_m))
print("="*40)

print("Prueba 22: For + for interno")
print(analizar_complejidad(algo_for_y_for_interno))
print("="*40)

print("Prueba 23: Repeat multiplicando por 3")
print(analizar_complejidad(algo_repeat_log_base3))
print("="*40)

print("Prueba 24: While hasta length(A)")
print(analizar_complejidad(algo_while_length))
print("="*40)

print("Prueba 25: Call swap en n^2")
print(analizar_complejidad(algo_call_swap_n2))
print("="*40)

print("Prueba 26: Call O(n) + log interno en for")
print(analizar_complejidad(algo_mixto_call_y_log))
print("="*40)

print("Prueba 27: If con rama n^2 y otra O(1)")
print(analizar_complejidad(algo_if_pesado))
print("="*40)

print("Prueba 28: For hasta m")
print(analizar_complejidad(algo_for_m))
print("="*40)

print("Prueba 29: Doble for n y m")
print(analizar_complejidad(algo_for_n_y_m))
print("="*40)

print("Prueba 30: Recursión 3 llamadas + trabajo lineal")
print(analizar_complejidad(algo_recursion_3_llamadas, nombre_funcion="algoritmo"))
print("="*40)



# --- Ejecución DP ---
print("="*40)
print("DP 1: Tabla 1D con for n")
print(analizar_complejidad(algo_dp_1d))
print("="*40)

print("DP 2: Tabla 2D con doble for")
print(analizar_complejidad(algo_dp_2d))
print("="*40)

print("DP 3: Memoización 1D sin bucles")
print(analizar_complejidad(algo_dp_memo_1d))
print("="*40)

print("DP 4: Memoización 2D sin bucles")
print(analizar_complejidad(algo_dp_memo_2d))
print("="*40)

print("DP 5: 2D n x n con transiciones O(1)")
print(analizar_complejidad(algo_dp_2d_n2))
print("="*40)

print("DP 6: 1D con while log interno")
print(analizar_complejidad(algo_dp_1d_log))
print("="*40)



print("="*40)
print("BnB 1: Subconjuntos con poda (bound >= best)")
print(analizar_complejidad(algo_bnb_subsets, nombre_funcion="algoritmo"))
print("="*40)

print("BnB 2: TSP con poda por lower bound")
print(analizar_complejidad(algo_bnb_tsp, nombre_funcion="algoritmo"))
print("="*40)

print("BnB 3: Knapsack con poda y n/2")
print(analizar_complejidad(algo_bnb_knapsack, nombre_funcion="algoritmo"))
print("="*40)

# juntar todas las pruebas en un string para pasarselo al llm como contexto
all_tests_code = "\n\n".join([
    "    USA EXCLUSIVAMENTE ESTA GRAMÁTICA PARA TODOS LOS EJEMPLOS \n",
    "",
    algo_constante,
    algo_lineal,
    algo_cuadratico,
    algo_condicional,
    algo_while_lineal,
    algo_repeat_log,
    algo_busqueda_binaria,
    algo_merge_sort,
    algo_busqueda_arreglo,
    algo_con_declaraciones,
    algo_lineal_con_declaraciones,
    algo_call_o1,
    algo_call_on,
    algo_call_anidado,
    algo_call_merge_sort_detallado,
    algo_for_n2,
    algo_cubico,
    algo_while_log,
    algo_for_con_log_interno,
    algo_if_balanceado,
    algo_for_length_m,
    algo_for_y_for_interno,
    algo_repeat_log_base3,
    algo_while_length,
    algo_call_swap_n2,
    algo_mixto_call_y_log,
    algo_if_pesado,
    algo_for_m,
    algo_for_n_y_m,
    algo_recursion_3_llamadas,
    algo_dp_1d,
    algo_dp_2d,
    algo_dp_memo_1d,
    algo_dp_memo_2d,
    algo_dp_2d_n2,
    algo_dp_1d_log,
    algo_bnb_subsets,
    algo_bnb_tsp,
    algo_bnb_knapsack
])