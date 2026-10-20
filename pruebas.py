# Pruebas del proyecto.
#   python pruebas.py
#
# 1. Frases que SI y que NO estan en el lenguaje de la gramatica en ingles.
# 2. Expresiones para la gramatica del profe (1.txt).
# 3. Verificacion de que la conversion a CNF no cambia el lenguaje: se generan
#    todas las cadenas cortas de la gramatica ORIGINAL (por fuerza bruta, con
#    derivaciones por la izquierda) y se compara contra lo que acepta el CYK
#    con la gramatica en CNF, probando TODAS las cadenas posibles hasta cierto
#    largo.
# 4. Tiempo del CYK segun el largo de la frase.

import os
import sys
import time
from itertools import product

from gramatica import leer_gramatica
from cnf import convertir_a_cnf, es_cnf
from cyk import cyk, preparar_indices, contar_arboles
from main import tokenizar

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CARPETA = os.path.dirname(os.path.abspath(__file__))

INGLES_SI = [
    "She eats a cake with a fork",
    "The cat drinks the beer",
    "he cooks",
    "she eats",
    "The dog eats the meat",
    "he cuts the cake with a knife",
    "She cooks the soup in the oven",
    "the cat drinks the juice with a spoon",
    "he eats a cake with a fork in the oven",
    "the dog cuts a meat with a knife with a fork",
    "She drinks the beer.",
    "A cat eats a dog",
    "he eats in the oven",
]

INGLES_NO = [
    "",
    "she",
    "eats",
    "the cat",
    "cat drinks the beer",          # falta el determinante
    "She eats cake",                # 'cake' sin determinante
    "the cat the dog",
    "He eats a cake with",          # PP incompleto
    "she eats a fork a knife",
    "The cat drinks the milk",      # 'milk' no esta en el vocabulario
    "eats she the cake",
    "she he eats",
    "with a fork she eats a cake",  # PP al inicio
    "she eats the the cake",
    "a the cat drinks",
]

EXPR_SI = ["id", "id + id", "id * id", "id + id * id", "( id )", "( id + id ) * id",
           "( ( id ) )", "id * ( id + id ) * id", "id + id + id + id"]
EXPR_NO = ["", "+", "id +", "id id", "( id", "id )", "( )", "* id", "id + * id", "( id + ) id"]


def correr_casos(nombre_archivo, casos_si, casos_no):
    # corre cada frase y compara con el resultado esperado
    g = leer_gramatica(os.path.join(CARPETA, "gramaticas", nombre_archivo))
    g_cnf, aux = convertir_a_cnf(g)
    indices = preparar_indices(g_cnf)
    terminales = [t.lower() for t in g_cnf.terminales()]
    print("\n### Gramatica: %s  (es CNF: %s)" % (nombre_archivo, es_cnf(g_cnf)))
    print("%-48s %-9s %-9s %-7s %s" % ("Frase", "Esperado", "Obtenido", "Arboles", "Tiempo (ms)"))
    print("-" * 90)
    bien = 0
    total = 0
    for frase, esperado in [(f, True) for f in casos_si] + [(f, False) for f in casos_no]:
        palabras = tokenizar(frase, terminales)
        t0 = time.perf_counter()
        acepta, tabla = cyk(g_cnf, palabras, indices)
        t = (time.perf_counter() - t0) * 1000
        arboles = contar_arboles(tabla, g_cnf.inicial, 0, len(palabras) - 1) if acepta and palabras else 0
        ok = acepta == esperado
        bien += ok
        total += 1
        mostrar = '"%s"' % frase if frase else '"" (vacia)'
        print("%-48s %-9s %-9s %-7s %.4f %s" % (mostrar, "SÍ" if esperado else "NO",
                                                "SÍ" if acepta else "NO", arboles, t,
                                                "" if ok else "  <-- FALLO"))
    print("Correctas: %d/%d" % (bien, total))
    return bien == total


# ---------------------------------------------------------------------------
# Generacion por fuerza bruta del lenguaje de la gramatica ORIGINAL
# ---------------------------------------------------------------------------
def generar_lenguaje(g, max_largo):
    """Todas las cadenas de largo <= max_largo que genera g (sin convertirla).
    Se expanden siempre la variable de mas a la izquierda y se podan las formas
    que ya tienen demasiados terminales o que son demasiado largas."""
    resultado = set()
    inicial = (g.inicial,)
    vistos = {inicial}
    pila = [inicial]
    limite_forma = 3 * max_largo + 3
    while pila:
        forma = pila.pop()
        # buscar la primera variable
        pos = -1
        for i, s in enumerate(forma):
            if g.es_variable(s):
                pos = i
                break
        if pos == -1:
            # ya no tiene variables, es una cadena del lenguaje
            resultado.add(forma)
            continue
        for cuerpo in g.producciones[forma[pos]]:
            nueva = forma[:pos] + cuerpo + forma[pos + 1:]
            num_terminales = sum(1 for s in nueva if not g.es_variable(s))
            if num_terminales > max_largo or len(nueva) > limite_forma:
                continue
            # el prefijo de terminales ya no cambia, si es muy largo se poda
            if nueva not in vistos:
                vistos.add(nueva)
                pila.append(nueva)
    return resultado


def verificar_equivalencia(nombre_archivo, max_largo):
    # prueba todas las combinaciones de terminales y compara lo que acepta el
    # CYK (con la CNF) contra lo que genera la gramatica original
    g = leer_gramatica(os.path.join(CARPETA, "gramaticas", nombre_archivo))
    g_cnf, _ = convertir_a_cnf(g)
    indices = preparar_indices(g_cnf)
    terminales = g.terminales()

    lenguaje = generar_lenguaje(g, max_largo)
    errores = 0
    probadas = 0
    aceptadas = 0
    for largo in range(0, max_largo + 1):
        for cadena in product(terminales, repeat=largo):
            probadas += 1
            acepta, _ = cyk(g_cnf, list(cadena), indices)
            aceptadas += acepta
            if acepta != (cadena in lenguaje):
                errores += 1
                if errores <= 5:
                    print("   diferencia en: '%s' (original: %s, CNF: %s)"
                          % (" ".join(cadena), cadena in lenguaje, acepta))
    print("%-12s largo <= %d: %6d cadenas probadas, %4d en el lenguaje, %d diferencias -> %s"
          % (nombre_archivo, max_largo, probadas, aceptadas, errores, "OK" if errores == 0 else "FALLO"))
    return errores == 0


def medir_tiempos():
    g = leer_gramatica(os.path.join(CARPETA, "gramaticas", "ingles.txt"))
    g_cnf, _ = convertir_a_cnf(g)
    indices = preparar_indices(g_cnf)
    print("\n### Tiempo del CYK vs largo de la frase (mejor de 20 corridas)")
    print("%-8s %-12s %s" % ("Palabras", "Tiempo (ms)", "Frase"))
    # se le van agregando "with a fork" al final para hacerla mas larga
    for repeticiones in [0, 1, 2, 4, 8, 16, 32]:
        frase = ["she", "eats", "a", "cake"] + ["with", "a", "fork"] * repeticiones
        mejores = []
        for _ in range(20):
            t0 = time.perf_counter()
            acepta, _ = cyk(g_cnf, frase, indices)
            mejores.append((time.perf_counter() - t0) * 1000)
        t = min(mejores)  # el minimo es mas estable que el promedio (menos ruido del sistema)
        texto = " ".join(frase)
        if len(texto) > 60:
            texto = texto[:57] + "..."
        print("%-8d %-12.4f %s  [%s]" % (len(frase), t, texto, "SÍ" if acepta else "NO"))


def main():
    todo_bien = True
    print("=" * 90)
    print("1-2. Casos de prueba")
    todo_bien &= correr_casos("ingles.txt", INGLES_SI, INGLES_NO)
    todo_bien &= correr_casos("1.txt", EXPR_SI, EXPR_NO)

    print("\n" + "=" * 90)
    print("3. Verificacion: la gramatica original y su CNF generan el mismo lenguaje")
    print("   (esta parte tarda como un minuto porque prueba cientos de miles de cadenas)")
    todo_bien &= verificar_equivalencia("1.txt", 6)
    todo_bien &= verificar_equivalencia("extra.txt", 7)
    todo_bien &= verificar_equivalencia("ingles.txt", 4)

    print("\n" + "=" * 90)
    medir_tiempos()

    print("\n" + ("TODAS LAS PRUEBAS PASARON" if todo_bien else "HAY PRUEBAS QUE FALLARON"))


if __name__ == "__main__":
    main()
