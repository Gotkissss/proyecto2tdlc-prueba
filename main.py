# Proyecto 2 - Teoria de la Computacion
# Parser CYK para una gramatica libre de contexto.
#
# Lee la gramatica, la pasa a CNF, y por cada frase corre el CYK y muestra
# SI/NO, el tiempo y el arbol de parseo.
#
# Uso:
#   python main.py                                   (modo interactivo con la gramatica en ingles)
#   python main.py "She eats a cake with a fork"     (una sola frase)
#   python main.py -g gramaticas/1.txt "id + id * id"
#   python main.py --tabla --pasos                   (muestra la tabla CYK y los pasos de la CNF)

import argparse
import os
import sys
import time

from gramatica import leer_gramatica, guardar_gramatica
from cnf import convertir_a_cnf, es_cnf
from cyk import cyk, preparar_indices, construir_arbol, contar_arboles, todos_los_arboles, imprimir_tabla
from arbol import imprimir_arbol, a_corchetes, arbol_original, guardar_imagen

# para que se vean bien las tildes y los dibujitos del arbol en la consola de Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# carpeta del proyecto, para encontrar gramaticas/ y arboles/ desde donde sea
CARPETA = os.path.dirname(os.path.abspath(__file__))
SIGNOS = ".,;:!?"


def tokenizar(frase, terminales):
    # separa por espacios y pasa a minusculas. Los signos de puntuacion pegados
    # a la palabra se quitan, a menos que el signo sea un terminal de la gramatica
    # (por ejemplo '(' y ')' en la gramatica de expresiones).
    terminales = set(t.lower() for t in terminales)
    palabras = []
    for w in frase.split():
        w = w.lower()
        if w not in terminales:
            limpia = w.strip(SIGNOS)
            if limpia == "":
                continue
            w = limpia
        palabras.append(w)
    return palabras


def analizar(frase, g_cnf, auxiliares, indices, terminales, opciones, num=1):
    # analiza una frase y muestra todo; num es el numero de frase (para el
    # nombre de la imagen)
    palabras = tokenizar(frase, terminales)
    print("\nFrase: " + frase)
    print("Palabras: " + str(palabras))

    desconocidas = [w for w in palabras if w not in terminales]

    # solo se mide el CYK
    inicio = time.perf_counter()
    acepta, tabla = cyk(g_cnf, palabras, indices)
    fin = time.perf_counter()
    tiempo_ms = (fin - inicio) * 1000

    print("Resultado: " + ("SÍ" if acepta else "NO") + " pertenece al lenguaje")
    print("Tiempo del algoritmo CYK: %.4f ms (%.7f s)" % (tiempo_ms, fin - inicio))
    if desconocidas:
        print("Palabras que no estan en el vocabulario de la gramatica: " + ", ".join(desconocidas))

    if opciones.tabla and palabras:
        print("\nTabla CYK (cada celda tiene las variables que generan ese pedazo):")
        imprimir_tabla(tabla, palabras)

    if not acepta or not palabras:
        return acepta, tiempo_ms

    n = len(palabras)
    cantidad = contar_arboles(tabla, g_cnf.inicial, 0, n - 1)
    if cantidad > 1:
        print("\nLa frase es AMBIGUA: tiene %d arboles de parseo distintos." % cantidad)

    arboles = todos_los_arboles(tabla, g_cnf.inicial, 0, n - 1, limite=opciones.max_arboles)
    for idx, arbol_cnf in enumerate(arboles, start=1):
        if len(arboles) > 1:
            print("\n========== Arbol %d de %d ==========" % (idx, cantidad))
        print("\nArbol de parseo (gramatica en CNF):")
        imprimir_arbol(arbol_cnf)
        if auxiliares:
            # el mismo arbol pero sin las variables que invento la CNF
            arbol_og = arbol_original(arbol_cnf, auxiliares)
            print("\nArbol sin las variables auxiliares de la CNF:")
            imprimir_arbol(arbol_og)
        print("\nNotacion de corchetes: " + a_corchetes(arbol_cnf))

        if not opciones.sin_imagen:
            nombre = "arbol_%d" % num if len(arboles) == 1 else "arbol_%d_%d" % (num, idx)
            ruta = guardar_imagen(arbol_cnf, os.path.join(CARPETA, "arboles", nombre), frase)
            print("Imagen del arbol guardada en: " + ruta)
    return acepta, tiempo_ms


def main():
    parser = argparse.ArgumentParser(description="Parser CYK - Proyecto 2 Teoria de la Computacion")
    parser.add_argument("frase", nargs="*", help="frase a analizar (si no se pone, entra en modo interactivo)")
    parser.add_argument("-g", "--gramatica", default=os.path.join(CARPETA, "gramaticas", "ingles.txt"),
                        help="archivo con la gramatica (default: gramaticas/ingles.txt)")
    parser.add_argument("--pasos", action="store_true", help="mostrar cada paso de la conversion a CNF")
    parser.add_argument("--tabla", action="store_true", help="mostrar la tabla del CYK")
    parser.add_argument("--sin-imagen", action="store_true", help="no generar la imagen del arbol")
    parser.add_argument("--max-arboles", type=int, default=3,
                        help="cuantos arboles mostrar como maximo si la frase es ambigua (default 3)")
    opciones = parser.parse_args()

    g = leer_gramatica(opciones.gramatica)
    print("=" * 60)
    print("Gramatica original (" + os.path.basename(opciones.gramatica) + "):")
    print(g)
    print("=" * 60)

    # la conversion se mide aparte del CYK
    inicio = time.perf_counter()
    g_cnf, auxiliares = convertir_a_cnf(g, verbose=opciones.pasos)
    tiempo_cnf = (time.perf_counter() - inicio) * 1000
    print("\nGramatica en Forma Normal de Chomsky:")
    print(g_cnf)
    print("(%d producciones, %d variables; conversion en %.3f ms; es CNF: %s)"
          % (g_cnf.num_producciones(), len(g_cnf.variables()), tiempo_cnf, "si" if es_cnf(g_cnf) else "NO"))

    # ingles.txt -> ingles-cnf.txt
    base, ext = os.path.splitext(opciones.gramatica)
    ruta_cnf = base + "-cnf" + ext
    guardar_gramatica(g_cnf, ruta_cnf)
    print("Guardada en: " + ruta_cnf)
    print("=" * 60)

    indices = preparar_indices(g_cnf)
    terminales = [t.lower() for t in g_cnf.terminales()]

    if opciones.frase:
        acepta, _ = analizar(" ".join(opciones.frase), g_cnf, auxiliares, indices, terminales, opciones)
        return

    print("\nModo interactivo. Escriba una frase (o 'salir' para terminar).")
    num = 1
    while True:
        try:
            frase = input("\nw = ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if frase.strip().lower() in ("salir", "exit", "q"):
            break
        analizar(frase, g_cnf, auxiliares, indices, terminales, opciones, num)
        num += 1


if __name__ == "__main__":
    main()
