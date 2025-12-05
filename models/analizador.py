import re
import math

# -----------------------------------------------------------------------------
# ANALIZADOR DE COMPLEJIDAD
# -----------------------------------------------------------------------------
# Este módulo provee un analizador heurístico de complejidad para pseudocódigo
# con construcciones tipo: begin/end, for/while/repeat, if/else, return y CALL.
# 
# Modelo de complejidad:
# - Representamos O(n^a log^b n) mediante la clase Complejidad (a = grado, b = log_factor).
# - La suma asintótica elige el término dominante (máximo por orden).
# - El producto suma grados y factores de logaritmo.
# 
# Flujo general:
# - analizar_complejidad: despachador que limpia el cuerpo principal y decide si
#   es iterativo o recursivo (divide y vencerás / branch and bound).
# - analizar_iterativo: recorre línea a línea, mantiene una pila de scopes,
#   acumula costos de peor y mejor caso, y aplica reglas para bucles y condicionales.
# - analizar_recursividad: detecta llamadas recursivas a la misma función, intenta
#   inferir a (ramificación) y b (divisor), estima f(n) con el analizador iterativo y
#   aplica Teorema Maestro o heurística de Branch & Bound.
# 
# Soporte adicional:
# - Programación dinámica (DP): detección de accesos a tablas 1D/2D y memoización,
#   con una heurística para contar costo por celda (O(1) por transición) y por número
#   de estados cuando no hay bucles explícitos.
# -----------------------------------------------------------------------------


class Complejidad:
    """Tipo para representar O(n^a log^b n) y operar asintóticamente."""
    def __init__(self, grado=0.0, log_factor=0):
        self.grado = float(grado)
        self.log_factor = int(log_factor)

    def __repr__(self):
        if math.isclose(self.grado, 0.0) and self.log_factor == 0: return "1"
        if math.isclose(self.grado, 0.0): return "log(n)" if self.log_factor == 1 else f"log^{self.log_factor}(n)"
        term_n = "n" if math.isclose(self.grado, 1.0) else f"n^{self.grado:g}"
        term_log = "" if self.log_factor == 0 else ("log(n)" if self.log_factor == 1 else f"log^{self.log_factor}(n)")
        return f"{term_n}{' ' if term_log else ''}{term_log}".strip()

    def dominio(self):
        return (self.grado, self.log_factor)

    def __add__(self, other):
        return self if self.dominio() >= other.dominio() else other

    def __mul__(self, other):
        return Complejidad(self.grado + other.grado, self.log_factor + other.log_factor)

    @staticmethod
    def constante(): return Complejidad(0.0, 0)
    @staticmethod
    def lineal(): return Complejidad(1.0, 0)
    @staticmethod
    def log(): return Complejidad(0.0, 1)


# -----------------------------------------------------------------------------
# SUBRUTINAS CONOCIDAS
# -----------------------------------------------------------------------------
SUBRUTINAS_COMPLEJIDAD = {
    'combinar': Complejidad(grado=1),
    'busqueda_lineal': Complejidad(grado=1),
    'swap': Complejidad(grado=0),
    'imprimir': Complejidad(grado=0),
}


def analizar_iterativo(pseudocodigo):
    """Analiza pseudocódigo imperativo (no recursivo) y estima complejidad."""
    lineas = pseudocodigo.strip().split('\n')
    pila_scope = []
    costos_acumulados = [{'peor': Complejidad.constante(), 'mejor': Complejidad.constante()}]

    # Regex patterns
    RE_DECLARACION = re.compile(r'^\s*([A-Z]\w*\s+)?\w+(\[\w*(\]\[\w*)*\])?\s*$')
    RE_CALL = re.compile(r'CALL\s+(\w+)\s*\((.*?)\)', re.IGNORECASE)
    RE_FOR = re.compile(r'for\s+(\w+)\s*🡨\s*([-\w]+)\s+to\s+([^\s]+)\s+do', re.IGNORECASE)
    RE_WHILE = re.compile(r'while\s+\((.+)\)\s+do', re.IGNORECASE)
    RE_REPEAT = re.compile(r'^\s*repeat\s*$', re.IGNORECASE)
    RE_IF = re.compile(r'^\s*if\s+\(.+\)\s+then\s*$', re.IGNORECASE)
    RE_ELSE = re.compile(r'^\s*else\s*$', re.IGNORECASE)
    RE_END = re.compile(r'^\s*end\s*$', re.IGNORECASE)
    RE_UNTIL = re.compile(r'^\s*until\s*\(.+\)\s*$', re.IGNORECASE)
    RE_ASSIGN = re.compile(r'^\s*\w+(\[\w+\])?\s*🡨')
    RE_ARRAY_ACCESS = re.compile(r'\w+\s*\[\s*\w+\s*\]')
    RE_COMPARE = re.compile(r'[<>=!]=?|≤|≥')
    RE_RETURN = re.compile(r'^\s*return\b', re.IGNORECASE)
    RE_HINT = re.compile(r'►\s*O\((.+?)\)', re.IGNORECASE)

    # DP patterns
    RE_DP_ACCESS_1D = re.compile(r'\b\w+\s*\[\s*\w+\s*\]')
    RE_DP_ACCESS_2D = re.compile(r'\b\w+\s*\[\s*\w+\s*\]\s*\[\s*\w+\s*\]')
    RE_MEMO_READ = re.compile(r'if\s*\(\s*\w+\s*\[\s*[^]]+\s*\]\s*(!=|==)\s*\w+\s*\)\s*then', re.IGNORECASE)
    RE_MEMO_WRITE = re.compile(r'\b\w+\s*\[\s*[^]]+\s*\]\s*🡨')
    RE_MIN_MAX_TRANSITION = re.compile(r'\b(min|max)\s*\(', re.IGNORECASE)

    dp_context = {
        'table_access': False,
        'memoization': False,
        'dimensions': 0,
        'transition_cost': Complejidad.constante(),
        'loops_active_dims': 0,
    }

    def parse_size_expr(expr: str) -> Complejidad:
        e = expr.strip().lower()
        if re.fullmatch(r'\d+', e): return Complejidad.constante()
        if re.fullmatch(r'length\(\w+\)', e): return Complejidad.lineal()
        m_pow = re.fullmatch(r'n\^(\d+(\.\d+)?)', e)
        if m_pow: return Complejidad(grado=float(m_pow.group(1)))
        if e in ('n', 'm'): return Complejidad.lineal()
        if re.fullmatch(r'n\*m', e): return Complejidad(2.0, 0)
        if re.fullmatch(r'(n|m)\s*/\s*\d+', e): return Complejidad.lineal()
        return Complejidad.lineal()

    def detect_update_pattern(var: str, linea: str):
        if re.search(fr'^{var}\s*🡨\s*{var}\s*\+\s*\d+', linea): return 'linear'
        if re.search(fr'^{var}\s*🡨\s*{var}\s*\-\s*\d+', linea): return 'linear'
        if re.search(fr'^{var}\s*🡨\s*{var}\s*[*]\s*\d+', linea): return 'log'
        if re.search(fr'^{var}\s*🡨\s*{var}\s*/\s*\d+', linea): return 'log'
        return None

    for i, raw in enumerate(lineas):
        linea = raw.strip()
        if not linea: continue

        m_hint = RE_HINT.search(linea)
        if m_hint:
            hint = m_hint.group(1).strip().lower()
            comp = Complejidad.constante()
            if 'n^' in hint:
                mk = re.search(r'n\^(\d+(\.\d+)?)', hint)
                comp = Complejidad(float(mk.group(1)), 0) if mk else Complejidad.lineal()
            elif 'log' in hint and 'n' in hint:
                comp = Complejidad.log()
            elif re.search(r'\bn\b', hint):
                comp = Complejidad.lineal()
            costos_acumulados[-1]['peor'] += comp
            costos_acumulados[-1]['mejor'] += comp
            continue

        if linea.startswith('►'): continue

        if RE_DP_ACCESS_2D.search(linea):
            dp_context['table_access'] = True
            dp_context['dimensions'] = max(dp_context['dimensions'], 2)
        elif RE_DP_ACCESS_1D.search(linea):
            dp_context['table_access'] = True
            dp_context['dimensions'] = max(dp_context['dimensions'], 1)
        if RE_MEMO_READ.search(linea) or RE_MEMO_WRITE.search(linea):
            dp_context['memoization'] = True
        if RE_MIN_MAX_TRANSITION.search(linea):
            dp_context['transition_cost'] = max(dp_context['transition_cost'], Complejidad.constante(), key=lambda c: c.dominio())

        if len(pila_scope) == 0 and linea == 'begin':
            pila_scope.append(('PRINCIPAL', None))
            continue

        if len(pila_scope) == 1 and pila_scope[-1][0] == 'PRINCIPAL':
            if (RE_DECLARACION.match(linea) and '🡨' not in linea and
                not re.search(r'(for|while|repeat|if|CALL)', linea, re.IGNORECASE)):
                continue

        m_for = RE_FOR.search(linea)
        m_while = RE_WHILE.search(linea)
        m_repeat = RE_REPEAT.search(linea)
        m_if = RE_IF.search(linea)
        is_else = RE_ELSE.match(linea) is not None
        is_end = RE_END.match(linea) is not None
        m_until = RE_UNTIL.search(linea)
        m_call = RE_CALL.search(linea)

        if m_for:
            var, start, stop = m_for.groups()
            iters = parse_size_expr(stop)
            pila_scope.append(('FOR', {'iters': iters, 'var': var}))
            costos_acumulados.append({'peor': Complejidad.constante(), 'mejor': Complejidad.constante()})
            dp_context['loops_active_dims'] = min(2, dp_context['loops_active_dims'] + 1)
            continue

        if m_while:
            cond = m_while.group(1)
            m_var = re.search(r'(\w+)\s*[<>=!≤≥]', cond)
            var = m_var.group(1) if m_var else None
            pila_scope.append(('WHILE', {'var': var, 'iters': Complejidad.lineal()}))
            costos_acumulados.append({'peor': Complejidad.constante(), 'mejor': Complejidad.constante()})
            continue

        if m_repeat:
            pila_scope.append(('REPEAT', {'var': None, 'iters': Complejidad.lineal()}))
            costos_acumulados.append({'peor': Complejidad.constante(), 'mejor': Complejidad.constante()})
            continue

        if m_if:
            pila_scope.append(('IF', None))
            costos_acumulados.append({'peor': Complejidad.constante(), 'mejor': Complejidad.constante()})
            continue

        if is_else:
            if not pila_scope or pila_scope[-1][0] != 'IF': continue
            costo_if = costos_acumulados.pop()
            pila_scope[-1] = ('ELSE', {'costo_if': costo_if})
            costos_acumulados.append({'peor': Complejidad.constante(), 'mejor': Complejidad.constante()})
            continue

        if pila_scope:
            tipo, meta = pila_scope[-1]
            if tipo in ('WHILE', 'REPEAT'):
                var = meta.get('var')
                if not var:
                    m_asg = re.search(r'^(\w+)\s*🡨', linea)
                    if m_asg: meta['var'] = m_asg.group(1)
                    var = meta.get('var')
                upd = detect_update_pattern(var, linea) if var else None
                if upd == 'log':
                    meta['iters'] = Complejidad.log()
                elif upd == 'linear':
                    meta['iters'] = Complejidad.lineal()

        if is_end or m_until:
            if is_end and (i + 1 < len(lineas)) and (lineas[i+1].strip() == 'else' or lineas[i+1].strip().startswith('until')):
                continue
            if not pila_scope: continue
            tipo_bloque, datos_bloque = pila_scope.pop()

            if tipo_bloque == 'PRINCIPAL': break

            costo_bloque_actual = costos_acumulados.pop()
            padre = costos_acumulados[-1]

            if tipo_bloque in ('FOR', 'WHILE', 'REPEAT'):
                iters = datos_bloque.get('iters', Complejidad.lineal())
                padre['peor'] += costo_bloque_actual['peor'] * iters
                padre['mejor'] += costo_bloque_actual['mejor'] * iters
                if tipo_bloque == 'FOR' and dp_context['loops_active_dims'] > 0:
                    dp_context['loops_active_dims'] -= 1

            elif tipo_bloque == 'IF':
                padre['peor'] += costo_bloque_actual['peor']
                padre['mejor'] += costo_bloque_actual['mejor']

            elif tipo_bloque == 'ELSE':
                costo_if = datos_bloque['costo_if']
                costo_else = costo_bloque_actual
                peor_rama = costo_if['peor'] if costo_if['peor'].dominio() >= costo_else['peor'].dominio() else costo_else['peor']
                mejor_rama = costo_if['mejor'] if costo_if['mejor'].dominio() <= costo_else['mejor'].dominio() else costo_else['mejor']
                padre['peor'] += peor_rama
                padre['mejor'] += mejor_rama

            continue

        costo_instr = Complejidad.constante()

        if RE_ASSIGN.search(linea): costo_instr = Complejidad.constante()
        if RE_ARRAY_ACCESS.search(linea): costo_instr = max(costo_instr, Complejidad.constante(), key=lambda c: c.dominio())
        if RE_COMPARE.search(linea): costo_instr = max(costo_instr, Complejidad.constante(), key=lambda c: c.dominio())
        if RE_RETURN.search(linea): costo_instr = max(costo_instr, Complejidad.constante(), key=lambda c: c.dominio())

        if m_call:
            nombre = m_call.group(1).lower()
            costo_instr = SUBRUTINAS_COMPLEJIDAD.get(nombre, Complejidad.constante())
            m_inline = RE_HINT.search(linea)
            if m_inline:
                hint_text = m_inline.group(1).lower()
                if 'n^' in hint_text:
                    k = float(re.search(r'n\^(\d+(\.\d+)?)', hint_text).group(1))
                    costo_instr = Complejidad(k, 0)
                elif 'log' in hint_text and 'n' in hint_text:
                    costo_instr = Complejidad.log()
                elif re.search(r'\bn\b', hint_text):
                    costo_instr = Complejidad.lineal()

        if dp_context['table_access'] and dp_context['loops_active_dims'] > 0:
            costo_instr = max(costo_instr, dp_context['transition_cost'], key=lambda c: c.dominio())

        costos_acumulados[-1]['peor'] += costo_instr
        costos_acumulados[-1]['mejor'] += costo_instr

    if dp_context['memoization'] and dp_context['table_access']:
        if dp_context['dimensions'] == 2:
            costos_acumulados[0]['peor'] += Complejidad(2.0, 0)
            costos_acumulados[0]['mejor'] += Complejidad(2.0, 0)
        elif dp_context['dimensions'] == 1:
            costos_acumulados[0]['peor'] += Complejidad.lineal()
            costos_acumulados[0]['mejor'] += Complejidad.lineal()

    resultado_final = costos_acumulados[0]
    peor_caso = resultado_final['peor']
    mejor_caso = resultado_final['mejor']
    if peor_caso.dominio() == mejor_caso.dominio():
        caso_promedio_str = f"Θ({peor_caso})"
    else:
        caso_promedio_str = f"Entre Ω({mejor_caso}) y O({peor_caso})"
    return { "Peor Caso (O)": f"O({peor_caso})", "Mejor Caso (Ω)": f"Ω({mejor_caso})", "Caso Promedio (Θ)": caso_promedio_str }


# -----------------------------------------------------------------------------
# 3. ANALIZADOR DE RECURSIVIDAD (ACTUALIZADO PARA RESTAS)
# -----------------------------------------------------------------------------
def analizar_recursividad(pseudocodigo, nombre_funcion):
    """Analiza recursividad del pseudocódigo (División y Sustracción)."""
    
    # 1. Factor de ramificación (a): número de llamadas a sí mismo
    a = len(re.findall(fr'CALL\s+{nombre_funcion}\s*\(', pseudocodigo, re.IGNORECASE))
    if a == 0:
        return None

    # 2. Detectar divisor (b) tipo n/k (n/2, n/3)
    match_b = re.search(fr'CALL\s+{nombre_funcion}\s*\([^)]*?\b\w+\s*/\s*(\d+)[^)]*\)', pseudocodigo, re.IGNORECASE)
    b = int(match_b.group(1)) if match_b else 1

    # 3. Detectar sustracción (k) tipo n - k (para T(n) = T(n-1) + ...)
    match_sub = re.search(fr'CALL\s+{nombre_funcion}\s*\([^)]*?\b\w+\s*-\s*(\d+)[^)]*\)', pseudocodigo, re.IGNORECASE)
    k_sub = int(match_sub.group(1)) if match_sub else 0
    if b <= 0: b = 1 # Salvaguarda

    # 4. Trabajo no recursivo f(n)
    codigo_no_recursivo = "\n".join([line for line in pseudocodigo.split('\n') if f'CALL {nombre_funcion}' not in line])
    lineas_filtradas = [line for line in codigo_no_recursivo.split('\n') if not re.match(r'^\s*algoritmo\(.*\)', line)]
    costo_extra_dict = analizar_iterativo('\n'.join(lineas_filtradas)) or {"Peor Caso (O)": "O(1)"}

    # Parsear f(n)
    costo_peor_str = costo_extra_dict.get('Peor Caso (O)', 'O(1)')
    match_f_n = re.search(r'O\((.*)\)', costo_peor_str)
    f_n_str = match_f_n.group(1) if match_f_n else "1"

    def parse_comp_str(s: str) -> Complejidad:
        s = s.lower()
        if 'n^' in s:
            mk = re.search(r'n\^(\d+(\.\d+)?)', s)
            return Complejidad(float(mk.group(1)), 1 if 'log' in s else 0) if mk else Complejidad.lineal()
        if 'log' in s and 'n' in s:
            return Complejidad.log()
        if re.search(r'\bn\b', s):
            return Complejidad.lineal()
        return Complejidad.constante()

    f_n = parse_comp_str(f_n_str)

    # 5. Lógica de Decisión

    # CASO: Recursión por Sustracción (T(n) = a T(n-k) + f(n))
    # Ej: XXX1(n-1)
    if k_sub > 0:
        if a == 1:
            # Lineal: T(n) = T(n-k) + f(n) -> Costo total ~ n/k * f(n)
            # Si f(n) es constante, queda O(n)
            total = Complejidad.lineal() * f_n
            return {
                "Análisis Recursivo": f"Relación: T(n) = T(n-{k_sub}) + O({f_n})",
                "Complejidad": f"Θ({total})"
            }
        elif a > 1:
            # Exponencial: T(n) = a T(n-k) + ... -> O(a^n)
            term = f"{a}^n"
            if k_sub > 1: term = f"{a}^(n/{k_sub})"
            return {
                "Análisis Recursivo": f"Relación: T(n) = {a}T(n-{k_sub}) + O({f_n})",
                "Complejidad": f"O({term})"
            }

    # CASO: Branch & Bound (heurístico)
    RE_BNB_COND = re.compile(r'\b(bound|cota|upper|lower|mejor|best)\b', re.IGNORECASE)
    RE_BNB_PRUNE = re.compile(r'if\s*\(.+?\)\s*then\s*(return|continue|skip)', re.IGNORECASE)
    hay_poda = bool(RE_BNB_COND.search(pseudocodigo)) and bool(RE_BNB_PRUNE.search(pseudocodigo))

    if hay_poda:
        peor_exponencial = f"O({a}^n)" if a > 1 and b == 1 else f"O(n^{math.log(a, b):.3g})" if (a > 1 and b > 1) else f"O({a}^n)"
        return {
            "Análisis Branch & Bound": f"Ramificación a={a}, divisor b={b}, poda detectada",
            "Peor Caso (O)": peor_exponencial,
            "Mejor Caso (Ω)": "Ω(n)",
            "Caso Promedio (Θ)": f"Entre Ω(n) y {peor_exponencial}"
        }

    # CASO: Teorema Maestro (División) T(n) = a T(n/b) + f(n)
    if b == 1:
        if a > 1:
            return { "Análisis Recursivo": f"T(n) ≈ {a}^n + O({f_n})", "Complejidad": f"Θ({a}^n)" }
        else:
            return { "Análisis Recursivo": f"T(n) = T(n) + O({f_n})", "Complejidad": f"Θ({f_n})" }

    # b > 1
    log_b_a = math.log(a, b) if a > 0 else 0.0
    resultado = Complejidad()
    if f_n.grado < log_b_a:
        resultado = Complejidad(grado=log_b_a)
    elif math.isclose(f_n.grado, log_b_a):
        resultado = Complejidad(grado=log_b_a, log_factor=f_n.log_factor + 1)
    else:
        resultado = f_n

    return {
        "Análisis Recursivo": f"Relación: T(n) = {a}T(n/{b}) + O({f_n})",
        "Complejidad": f"Θ({resultado})"
    }


# -----------------------------------------------------------------------------
# 4. UTILIDAD: LIMPIAR CUERPO PRINCIPAL
# -----------------------------------------------------------------------------
def limpiar_codigo_principal(pseudocodigo):
    lineas = pseudocodigo.split('\n')
    lineas_limpias = []
    dentro_subrutina = False
    RE_CLASE = re.compile(r'^\s*\w+\s*\{.*')
    RE_SUBRUTINA = re.compile(r'^\s*\w+\(.*\)')
    
    for linea in lineas:
        linea_strip = linea.strip()
        if RE_CLASE.match(linea_strip): continue
        if RE_SUBRUTINA.match(linea_strip):
            dentro_subrutina = True
            continue
        if linea_strip == 'end':
            if dentro_subrutina and len(lineas_limpias) > 0 and lineas_limpias[-1].strip() == 'begin':
                dentro_subrutina = False
                continue
        if not dentro_subrutina:
            lineas_limpias.append(linea)
            
    return '\n'.join(lineas_limpias)


def analizar_complejidad(pseudocodigo, nombre_funcion="algoritmo"):
    """Despacha el análisis según sea recursivo o no."""
    codigo_limpio = limpiar_codigo_principal(pseudocodigo)
    
    # Intenta detectar el nombre de la función si no es "algoritmo"
    # Si encuentra CALL XXX1, asume XXX1 es la función.
    if nombre_funcion == "algoritmo":
        m_call_custom = re.search(r'CALL\s+(\w+)', pseudocodigo)
        if m_call_custom:
            posible_nombre = m_call_custom.group(1)
            # Verifica si el call se refiere a la misma función (recursión)
            # Para simplificar, si hay un CALL a algo que no sea subrutina conocida, asumimos que es la recursiva.
            if posible_nombre not in SUBRUTINAS_COMPLEJIDAD:
                nombre_funcion = posible_nombre

    if f"CALL {nombre_funcion}" in pseudocodigo:
        print(f"--- Detectada recursividad en '{nombre_funcion}' ---")
        return analizar_recursividad(pseudocodigo, nombre_funcion)
    else:
        return analizar_iterativo(codigo_limpio)