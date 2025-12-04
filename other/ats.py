import re

# -----------------------------------------------------------------------------
# 1. CLASES DE NODOS PARA EL AST
# -----------------------------------------------------------------------------
class Node:
    pass

class ProgramNode(Node):
    def __init__(self, statements):
        self.statements = statements

class AssignmentNode(Node):
    def __init__(self, text):
        self.text = text

class ForLoopNode(Node):
    def __init__(self, limit, body):
        self.limit = limit
        self.body = body

class WhileLoopNode(Node):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class IfNode(Node):
    def __init__(self, condition, if_body, else_body=None):
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body

# -----------------------------------------------------------------------------
# 2. CLASE DE COMPLEJIDAD (Sin cambios)
# -----------------------------------------------------------------------------
class Complejidad:
    def __init__(self, grado=0, log_factor=0):
        self.grado = grado
        self.log_factor = log_factor
    def __repr__(self):
        if self.grado == 0 and self.log_factor == 0: return "1"
        if self.grado == 0: return f"log(n)" if self.log_factor == 1 else f"log^{self.log_factor}(n)"
        term_n = "n" if self.grado == 1 else f"n^{self.grado}"
        term_log = ""
        if self.log_factor > 0:
            term_log = "log(n)" if self.log_factor == 1 else f"log^{self.log_factor}(n)"
        return f"{term_n}{' ' if term_n and term_log else ''}{term_log}".strip()
    def __add__(self, other):
        if self.grado > other.grado: return self
        if other.grado > self.grado: return other
        return self if self.log_factor > other.log_factor else other
    def __mul__(self, other):
        return Complejidad(self.grado + other.grado, self.log_factor + other.log_factor)

# -----------------------------------------------------------------------------
# 3. EL PARSER
# -----------------------------------------------------------------------------
def parse(code_lines):
    clean_lines = []
    for line in code_lines:
        clean_line = line.split('►')[0].strip()
        if clean_line:
            clean_lines.append(clean_line)

    lines = clean_lines
    statements = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if line == 'begin':
            i += 1
            continue

        match_for = re.search(r'for\s+\w+\s*🡨\s*\d+\s+to\s+(length\(\w+\)|\w+)\s+do', line)
        match_while = re.search(r'while\s+\(?(.*)\)?\s+do', line)
        match_if = re.search(r'if\s+\(.*\)\s+then', line)
        
        if match_for:
            body_lines, end_index = extract_body(lines, i)
            body_ast = parse(body_lines)
            node = ForLoopNode(limit=match_for.group(1), body=body_ast)
            statements.append(node)
            i = end_index
        elif match_while:
            body_lines, end_index = extract_body(lines, i)
            body_ast = parse(body_lines)
            node = WhileLoopNode(condition=match_while.group(1), body=body_ast)
            statements.append(node)
            i = end_index
        elif match_if:
            if_body_lines, end_if_index = extract_body(lines, i)
            if end_if_index + 1 < len(lines) and lines[end_if_index + 1] == 'else':
                else_body_lines, end_else_index = extract_body(lines, end_if_index + 1)
                if_ast = parse(if_body_lines)
                else_ast = parse(else_body_lines)
                node = IfNode(condition=line, if_body=if_ast, else_body=else_ast)
                i = end_else_index
            else:
                if_ast = parse(if_body_lines)
                node = IfNode(condition=line, if_body=if_ast)
                i = end_if_index
            statements.append(node)
        elif line not in ['else', 'end'] and not line.startswith('until'):
            statements.append(AssignmentNode(line))

        i += 1
    return ProgramNode(statements)

def extract_body(lines, start_index):
    body_lines = []
    level = 0
    begin_index = -1
    for i in range(start_index, len(lines)):
        if lines[i] == 'begin':
            begin_index = i
            level = 1
            break
    if begin_index == -1: return [], start_index
    for i in range(begin_index + 1, len(lines)):
        line = lines[i]
        if line == 'begin': level += 1
        elif line == 'end': level -= 1
        if level == 0: return body_lines, i
        body_lines.append(line)
    return [], len(lines) - 1

# -----------------------------------------------------------------------------
# 4. EL ANALIZADOR
# -----------------------------------------------------------------------------
def analyze_ast(node):
    if isinstance(node, ProgramNode):
        costo = {'peor': Complejidad(), 'mejor': Complejidad()}
        for stmt in node.statements:
            stmt_cost = analyze_ast(stmt)
            costo['peor'] += stmt_cost['peor']
            costo['mejor'] += stmt_cost['mejor']
        return costo
    if isinstance(node, AssignmentNode):
        return {'peor': Complejidad(), 'mejor': Complejidad()}
    if isinstance(node, ForLoopNode):
        costo_cuerpo = analyze_ast(node.body)
        costo_iteraciones = Complejidad(grado=1)
        return {'peor': costo_cuerpo['peor'] * costo_iteraciones, 'mejor': costo_cuerpo['mejor'] * costo_iteraciones}
    if isinstance(node, WhileLoopNode):
        costo_cuerpo = analyze_ast(node.body)
        costo_iteraciones = Complejidad(grado=1)
        match_cond_var = re.search(r'(\w+)\s*[<>=!≤≥]', node.condition)
        if match_cond_var:
            variable = match_cond_var.group(1)
            for stmt in node.body.statements:
                if isinstance(stmt, AssignmentNode):
                    if re.search(fr'^{variable}\s*🡨\s*{variable}\s*([*\/])', stmt.text):
                        costo_iteraciones = Complejidad(log_factor=1)
                        break
        return {'peor': costo_cuerpo['peor'] * costo_iteraciones, 'mejor': costo_cuerpo['mejor'] * costo_iteraciones}
    if isinstance(node, IfNode):
        costo_if = analyze_ast(node.if_body)
        costo_else = analyze_ast(node.else_body) if node.else_body else {'peor': Complejidad(), 'mejor': Complejidad()}
        return {
            'peor': max(costo_if['peor'], costo_else['peor'], key=lambda c: (c.grado, c.log_factor)),
            'mejor': min(costo_if['mejor'], costo_else['mejor'], key=lambda c: (c.grado, c.log_factor))
        }

def analizar_complejidad(pseudocodigo):
    lineas = pseudocodigo.strip().split('\n')
    ast = parse(lineas)
    resultado = analyze_ast(ast)
    peor_caso = resultado['peor']
    mejor_caso = resultado['mejor']

    if peor_caso.grado == mejor_caso.grado and peor_caso.log_factor == mejor_caso.log_factor:
        caso_promedio_str = f"Θ({peor_caso})"
    else:
        caso_promedio_str = f"Entre Ω({mejor_caso}) y O({peor_caso})"

    return {"Peor Caso (O)": f"O({peor_caso})", "Mejor Caso (Ω)": f"Ω({mejor_caso})", "Caso Promedio (Θ)": caso_promedio_str}

# -----------------------------------------------------------------------------
# 5. CONJUNTO DE PRUEBAS COMPLETO
# -----------------------------------------------------------------------------

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

# Prueba 6 (aún no soportado por el parser de AST)
# algo_repeat_log = ...

# Prueba 9: Búsqueda lineal en un arreglo
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

# Prueba que fallaba antes: Bucle WHILE anidado dentro de un FOR
algo_for_while_anidado = """
begin
    suma 🡨 0
    for i 🡨 1 to n do
    begin
        j 🡨 1
        while (j < n) do
        begin
            suma 🡨 suma + 1
            j 🡨 j * 2
        end
    end
end
"""

# --- Ejecución de todas las pruebas ---
print("="*40)
print("Prueba 1: Análisis del Algoritmo Constante")
print(analizar_complejidad(algo_constante))
print("="*40)

print("\nPrueba 2: Análisis del Algoritmo Lineal (FOR)")
print(analizar_complejidad(algo_lineal))
print("="*40)

print("\nPrueba 3: Análisis del Algoritmo Cuadrático")
print(analizar_complejidad(algo_cuadratico))
print("="*40)

print("\nPrueba 4: Análisis del Algoritmo Condicional")
print(analizar_complejidad(algo_condicional))
print("="*40)

print("\nPrueba 5: Análisis del Bucle WHILE Lineal")
print(analizar_complejidad(algo_while_lineal))
print("="*40)

print("\nPrueba 9: Análisis de Búsqueda Lineal en Arreglo")
print(analizar_complejidad(algo_busqueda_arreglo))
print("="*40)

print("\nPrueba Adicional: FOR con WHILE anidado")
print(analizar_complejidad(algo_for_while_anidado))
print("="*40)