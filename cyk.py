# Algoritmo CYK (Cocke-Younger-Kasami).
#
# Idea (programacion dinamica): tabla[i][j] guarda las variables que pueden
# generar el pedazo de la frase que va de la palabra i a la palabra j.
#   - Largo 1: tabla[i][i] = { A | A -> palabra_i }
#   - Largo > 1: para cada punto de corte k entre i y j,
#       si B esta en tabla[i][k], C esta en tabla[k+1][j] y existe A -> B C,
#       entonces A va en tabla[i][j].
# La frase es aceptada si la variable inicial queda en tabla[0][n-1].
#
# En vez de guardar solo "si/no" en cada celda guardamos de donde salio cada
# variable (backpointers). Asi despues se puede armar el arbol de parseo.
#
# Complejidad: O(n^3 * |G|), n = numero de palabras.

from collections import defaultdict


def preparar_indices(g):
    # para no recorrer toda la gramatica en cada celda, armamos diccionarios:
    #   por_terminal['cat'] = ['N']
    #   por_par[('Det','N')] = ['NP']
    por_terminal = defaultdict(list)
    por_par = defaultdict(list)
    for var, cuerpos in g.producciones.items():
        for c in cuerpos:
            if len(c) == 1:
                por_terminal[c[0].lower()].append(var)
            elif len(c) == 2:
                por_par[c].append(var)
    return por_terminal, por_par


def cyk(g, palabras, indices=None):
    """Regresa (acepta, tabla).
    tabla[i][j] es un diccionario  variable -> lista de backpointers
    un backpointer es ('t', palabra) para las hojas o (k, B, C) para A -> B C"""
    n = len(palabras)
    if n == 0:
        # la cadena vacia solo es aceptada si S -> e
        return () in g.producciones.get(g.inicial, []), []

    if indices is None:
        indices = preparar_indices(g)
    por_terminal, por_par = indices

    tabla = [[{} for _ in range(n)] for _ in range(n)]

    # largo 1
    for i, w in enumerate(palabras):
        for a in por_terminal.get(w.lower(), []):
            tabla[i][i][a] = [("t", w)]

    # largos 2..n
    for largo in range(2, n + 1):
        for i in range(0, n - largo + 1):
            j = i + largo - 1
            celda = tabla[i][j]
            for k in range(i, j):
                izq = tabla[i][k]
                der = tabla[k + 1][j]
                if not izq or not der:
                    continue
                for b in izq:
                    for c in der:
                        for a in por_par.get((b, c), ()):
                            if a not in celda:
                                celda[a] = []
                            celda[a].append((k, b, c))

    acepta = g.inicial in tabla[0][n - 1]
    return acepta, tabla


def construir_arbol(tabla, var, i, j, opcion=0):
    """Arma el arbol de parseo usando los backpointers.
    Un nodo es una tupla (variable, [hijos]); un hijo puede ser otro nodo o un
    string (la palabra, que es una hoja)."""
    bp = tabla[i][j][var][opcion]
    if bp[0] == "t":
        return (var, [bp[1]])
    k, b, c = bp
    return (var, [construir_arbol(tabla, b, i, k), construir_arbol(tabla, c, k + 1, j)])


def contar_arboles(tabla, var, i, j, memo=None):
    # cuantos arboles de parseo distintos hay (si es > 1 la frase es ambigua)
    if memo is None:
        memo = {}
    clave = (var, i, j)
    if clave in memo:
        return memo[clave]
    total = 0
    for bp in tabla[i][j].get(var, []):
        if bp[0] == "t":
            total += 1
        else:
            k, b, c = bp
            total += contar_arboles(tabla, b, i, k, memo) * contar_arboles(tabla, c, k + 1, j, memo)
    memo[clave] = total
    return total


def todos_los_arboles(tabla, var, i, j, limite=10):
    # genera todos los arboles (hasta un limite, porque pueden ser muchisimos)
    resultado = []
    for bp in tabla[i][j].get(var, []):
        if bp[0] == "t":
            resultado.append((var, [bp[1]]))
        else:
            k, b, c = bp
            for izq in todos_los_arboles(tabla, b, i, k, limite):
                for der in todos_los_arboles(tabla, c, k + 1, j, limite):
                    resultado.append((var, [izq, der]))
                    if len(resultado) >= limite:
                        return resultado
        if len(resultado) >= limite:
            break
    return resultado


def imprimir_tabla(tabla, palabras):
    # imprime la tabla triangular, de abajo (largo 1) hacia arriba (largo n)
    n = len(palabras)
    if n == 0:
        return
    celdas = {}
    ancho = 6
    for i in range(n):
        for j in range(i, n):
            txt = ",".join(sorted(tabla[i][j].keys())) or "-"
            celdas[(i, j)] = txt
            ancho = max(ancho, len(txt) + 2)
    for w in palabras:
        ancho = max(ancho, len(w) + 2)
    ancho = min(ancho, 22)

    def corta(t):
        return t if len(t) <= ancho - 2 else t[: ancho - 4] + ".."

    for largo in range(n, 0, -1):
        fila = "largo %-2d|" % largo
        for i in range(0, n - largo + 1):
            fila += corta(celdas[(i, i + largo - 1)]).center(ancho) + "|"
        print(fila)
    print("        |" + "|".join(corta(w).center(ancho) for w in palabras) + "|")
