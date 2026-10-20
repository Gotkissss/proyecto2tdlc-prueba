# Funciones para mostrar el arbol de parseo: en consola, con corchetes y como
# imagen usando Graphviz (si esta instalado).
# Un nodo es (variable, [hijos]) y una hoja es el string de la palabra.

import os
import shutil
import subprocess


def imprimir_arbol(nodo, prefijo="", es_ultimo=True, es_raiz=True):
    # dibuja el arbol con ├── y └──; el prefijo lleva las lineas │ de los
    # niveles de arriba
    if isinstance(nodo, str):
        conector = "" if es_raiz else ("└── " if es_ultimo else "├── ")
        print(prefijo + conector + '"' + nodo + '"')
        return
    var, hijos = nodo
    if es_raiz:
        print(var)
        nuevo_prefijo = ""
    else:
        print(prefijo + ("└── " if es_ultimo else "├── ") + var)
        nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")
    for i, h in enumerate(hijos):
        imprimir_arbol(h, nuevo_prefijo, i == len(hijos) - 1, False)


def a_corchetes(nodo):
    # [S [NP she] [VP eats]]
    if isinstance(nodo, str):
        return nodo
    var, hijos = nodo
    return "[" + var + " " + " ".join(a_corchetes(h) for h in hijos) + "]"


def aplanar(nodo, auxiliares):
    """Quita los nodos de variables inventadas en la conversion a CNF (las de
    los pasos 4 y 5), metiendo sus hijos directamente en el padre. Asi el arbol
    se parece mas a la gramatica original (ej: F -> ( E ) en vez de F -> L Z)."""
    # regresa una lista porque un nodo auxiliar se "deshace" en varios hijos
    if isinstance(nodo, str):
        return [nodo]
    var, hijos = nodo
    nuevos_hijos = []
    for h in hijos:
        nuevos_hijos.extend(aplanar(h, auxiliares))
    if var in auxiliares:
        return nuevos_hijos
    return [(var, nuevos_hijos)]


def arbol_original(nodo, auxiliares):
    # la raiz nunca es auxiliar, asi que la lista siempre tiene un solo nodo
    return aplanar(nodo, auxiliares)[0]


def a_dot(nodo, titulo=""):
    # genera el texto del arbol en formato DOT (el que usa Graphviz)
    lineas = ["digraph arbol {", '  node [fontname="Helvetica"];']
    if titulo:
        lineas.append('  labelloc="t"; label="%s";' % titulo.replace('"', "'"))
    contador = [0]  # lista para poder modificarlo desde visitar()

    def visitar(n):
        # agrega el nodo y sus hijos, y regresa el id que se le dio
        mi_id = "n%d" % contador[0]
        contador[0] += 1
        if isinstance(n, str):
            etiqueta = n.replace('"', '\\"')
            lineas.append('  %s [label="%s", shape=plaintext, fontcolor="#1a5fb4"];' % (mi_id, etiqueta))
            return mi_id
        var, hijos = n
        lineas.append('  %s [label="%s", shape=ellipse];' % (mi_id, var))
        for h in hijos:
            hijo_id = visitar(h)
            lineas.append("  %s -> %s;" % (mi_id, hijo_id))
        return mi_id

    visitar(nodo)
    lineas.append("}")
    return "\n".join(lineas)


def guardar_imagen(nodo, ruta_sin_ext, titulo=""):
    """Guarda el .dot y si Graphviz esta instalado tambien el .png.
    Regresa la ruta del archivo generado."""
    carpeta = os.path.dirname(ruta_sin_ext)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    ruta_dot = ruta_sin_ext + ".dot"
    with open(ruta_dot, "w", encoding="utf-8") as f:
        f.write(a_dot(nodo, titulo))
    if shutil.which("dot"):
        ruta_png = ruta_sin_ext + ".png"
        try:
            # igual que correr: dot -Tpng arbol.dot -o arbol.png
            subprocess.run(["dot", "-Tpng", ruta_dot, "-o", ruta_png], check=True,
                           capture_output=True)
            return ruta_png
        except Exception:
            pass
    return ruta_dot
