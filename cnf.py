# Simplificacion de gramaticas y conversion a Forma Normal de Chomsky (CNF).
#
# Una gramatica esta en CNF si todas sus producciones son de la forma:
#   A -> B C      (dos variables)
#   A -> a        (un terminal)
#   S -> e        (solo la inicial, y solo si el lenguaje tiene la cadena vacia)
#
# Pasos que se hacen (en este orden):
#   1. Eliminar producciones epsilon (A -> e)
#   2. Eliminar producciones unitarias (A -> B)
#   3. Eliminar simbolos inutiles (no generadores y no alcanzables)
#   4. Reemplazar terminales en producciones largas (A -> a B  =>  A -> X B, X -> a)
#   5. Partir producciones de mas de 2 variables (A -> B C D  =>  A -> B Y, Y -> C D)

from itertools import product

from gramatica import Gramatica


class GeneradorNombres:
    # Da nombres nuevos para variables que no choquen con los que ya existen.
    # Primero intenta con letras sueltas (como hizo el profe en 1-cnf.txt) y si
    # ya no hay, usa X1, X2, ...
    def __init__(self, g):
        self.usados = set(g.variables()) | set(g.terminales())
        self.contador = 0

    def nuevo(self):
        for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if letra not in self.usados:
                self.usados.add(letra)
                return letra
        while True:
            self.contador += 1
            nombre = "X" + str(self.contador)
            if nombre not in self.usados:
                self.usados.add(nombre)
                return nombre


def log(verbose, texto=""):
    if verbose:
        print(texto)


# ---------------------------------------------------------------------------
# Paso 1: producciones epsilon
# ---------------------------------------------------------------------------
def anulables(g):
    # variables que pueden derivar epsilon (punto fijo)
    nul = set()
    cambio = True
    while cambio:
        cambio = False
        for var, cuerpos in g.producciones.items():
            if var in nul:
                continue
            for c in cuerpos:
                if all(s in nul for s in c):  # incluye el caso c == ()
                    nul.add(var)
                    cambio = True
                    break
    return nul


def eliminar_epsilon(g, nombres, verbose=False):
    nul = anulables(g)
    log(verbose, "  Variables anulables: " + (", ".join(sorted(nul)) if nul else "(ninguna)"))

    nueva = Gramatica(g.inicial, {v: [] for v in g.producciones})
    for var, cuerpos in g.producciones.items():
        for c in cuerpos:
            # para cada simbolo anulable hay 2 opciones: dejarlo o quitarlo
            opciones = []
            for s in c:
                if s in nul:
                    opciones.append([s, None])
                else:
                    opciones.append([s])
            for combinacion in product(*opciones):
                cuerpo = tuple(s for s in combinacion if s is not None)
                if len(cuerpo) > 0:
                    nueva.agregar(var, cuerpo)

    # si la inicial era anulable el lenguaje tiene la cadena vacia, entonces
    # hacemos una inicial nueva S0 -> S | e para no perderla
    if g.inicial in nul:
        s0 = nombres.nuevo()
        log(verbose, "  La inicial %s es anulable: se agrega %s -> %s | e" % (g.inicial, s0, g.inicial))
        prods = {s0: [(g.inicial,), ()]}
        prods.update(nueva.producciones)
        nueva = Gramatica(s0, prods)
    return nueva


# ---------------------------------------------------------------------------
# Paso 2: producciones unitarias
# ---------------------------------------------------------------------------
def pares_unitarios(g):
    # para cada A, el conjunto de B tal que A =>* B usando solo unitarias
    pares = {}
    for a in g.producciones:
        alcanzados = [a]
        i = 0
        while i < len(alcanzados):
            actual = alcanzados[i]
            for c in g.producciones.get(actual, []):
                if len(c) == 1 and g.es_variable(c[0]) and c[0] not in alcanzados:
                    alcanzados.append(c[0])
            i += 1
        pares[a] = alcanzados
    return pares


def eliminar_unitarias(g, verbose=False):
    pares = pares_unitarios(g)
    for a, lista in pares.items():
        if len(lista) > 1:
            log(verbose, "  %s =>* %s" % (a, ", ".join(lista[1:])))

    nueva = Gramatica(g.inicial, {v: [] for v in g.producciones})
    for a in g.producciones:
        for b in pares[a]:
            for c in g.producciones[b]:
                es_unitaria = len(c) == 1 and g.es_variable(c[0])
                if not es_unitaria:
                    nueva.agregar(a, c)
    return nueva


# ---------------------------------------------------------------------------
# Paso 3: simbolos inutiles
# ---------------------------------------------------------------------------
def generadores(g):
    # variables que pueden llegar a una cadena de puros terminales
    gen = set()
    cambio = True
    while cambio:
        cambio = False
        for var, cuerpos in g.producciones.items():
            if var in gen:
                continue
            for c in cuerpos:
                if all((not g.es_variable(s)) or s in gen for s in c):
                    gen.add(var)
                    cambio = True
                    break
    return gen


def alcanzables(g):
    vistos = [g.inicial]
    i = 0
    while i < len(vistos):
        for c in g.producciones.get(vistos[i], []):
            for s in c:
                if g.es_variable(s) and s not in vistos:
                    vistos.append(s)
        i += 1
    return set(vistos)


def eliminar_inutiles(g, verbose=False):
    # primero los no generadores (el orden importa!)
    gen = generadores(g)
    no_gen = [v for v in g.producciones if v not in gen]
    log(verbose, "  No generadoras: " + (", ".join(no_gen) if no_gen else "(ninguna)"))

    prods = {}
    for var, cuerpos in g.producciones.items():
        if var not in gen:
            continue
        prods[var] = []
        for c in cuerpos:
            if all((not g.es_variable(s)) or s in gen for s in c):
                prods[var].append(c)
    if g.inicial not in prods:
        # la inicial no genera nada: el lenguaje es vacio
        log(verbose, "  OJO: la variable inicial no genera ninguna cadena, el lenguaje es vacio")
        prods[g.inicial] = []
    g2 = Gramatica(g.inicial, prods)

    # despues los no alcanzables
    alc = alcanzables(g2)
    no_alc = [v for v in g2.producciones if v not in alc]
    log(verbose, "  No alcanzables: " + (", ".join(no_alc) if no_alc else "(ninguna)"))
    prods = {v: c for v, c in g2.producciones.items() if v in alc}
    return Gramatica(g.inicial, prods)


# ---------------------------------------------------------------------------
# Paso 4: terminales dentro de producciones de largo >= 2
# ---------------------------------------------------------------------------
def reemplazar_terminales(g, nombres, auxiliares, verbose=False):
    nueva = Gramatica(g.inicial, {v: [] for v in g.producciones})
    var_de_terminal = {}
    for var, cuerpos in g.producciones.items():
        for c in cuerpos:
            if len(c) < 2:
                nueva.agregar(var, c)
                continue
            nuevo_cuerpo = []
            for s in c:
                if g.es_variable(s):
                    nuevo_cuerpo.append(s)
                else:
                    if s not in var_de_terminal:
                        x = nombres.nuevo()
                        var_de_terminal[s] = x
                        auxiliares.add(x)
                        log(verbose, "  Nueva variable %s -> %s" % (x, s))
                    nuevo_cuerpo.append(var_de_terminal[s])
            nueva.agregar(var, tuple(nuevo_cuerpo))
    for t, x in var_de_terminal.items():
        nueva.agregar(x, (t,))
    return nueva


# ---------------------------------------------------------------------------
# Paso 5: partir producciones largas
# ---------------------------------------------------------------------------
def binarizar(g, nombres, auxiliares, verbose=False):
    nueva = Gramatica(g.inicial, {v: [] for v in g.producciones})
    var_de_cola = {}  # para reusar la misma variable si la cola se repite

    pendientes = []
    for var, cuerpos in g.producciones.items():
        for c in cuerpos:
            if len(c) <= 2:
                nueva.agregar(var, c)
            else:
                pendientes.append((var, c))

    # A -> B C D E  =>  A -> B Y1 ; Y1 -> C Y2 ; Y2 -> D E
    while pendientes:
        var, c = pendientes.pop(0)
        cola = c[1:]
        x = var_de_cola.get(cola)
        if x is None:
            x = nombres.nuevo()
            var_de_cola[cola] = x
            auxiliares.add(x)
            log(verbose, "  Nueva variable %s -> %s" % (x, " ".join(cola)))
            if len(cola) == 2:
                nueva.agregar(x, cola)
            else:
                pendientes.append((x, cola))
        nueva.agregar(var, (c[0], x))
    return nueva


# ---------------------------------------------------------------------------
def es_cnf(g):
    for var, cuerpos in g.producciones.items():
        for c in cuerpos:
            if len(c) == 0:
                if var != g.inicial:
                    return False
            elif len(c) == 1:
                if g.es_variable(c[0]):
                    return False
            elif len(c) == 2:
                if not (g.es_variable(c[0]) and g.es_variable(c[1])):
                    return False
            else:
                return False
    # si la inicial tiene epsilon no puede aparecer a la derecha
    if () in g.producciones.get(g.inicial, []):
        for cuerpos in g.producciones.values():
            for c in cuerpos:
                if g.inicial in c:
                    return False
    return True


def convertir_a_cnf(g, verbose=False):
    """Devuelve (gramatica_cnf, auxiliares).
    'auxiliares' son las variables que se inventaron en los pasos 4 y 5; sirven
    para reconstruir el arbol con la forma de la gramatica original."""
    nombres = GeneradorNombres(g)
    auxiliares = set()

    log(verbose, "Paso 1: eliminar producciones epsilon")
    g = eliminar_epsilon(g, nombres, verbose)
    log(verbose, indentar(g))

    log(verbose, "\nPaso 2: eliminar producciones unitarias")
    g = eliminar_unitarias(g, verbose)
    log(verbose, indentar(g))

    log(verbose, "\nPaso 3: eliminar simbolos inutiles")
    g = eliminar_inutiles(g, verbose)
    log(verbose, indentar(g))

    log(verbose, "\nPaso 4: reemplazar terminales en producciones de largo >= 2")
    g = reemplazar_terminales(g, nombres, auxiliares, verbose)
    log(verbose, indentar(g))

    log(verbose, "\nPaso 5: partir producciones de largo > 2")
    g = binarizar(g, nombres, auxiliares, verbose)
    log(verbose, indentar(g))

    return g, auxiliares


def indentar(g):
    texto = str(g)
    if texto == "":
        texto = "(sin producciones)"
    return "\n".join("    " + l for l in texto.splitlines())
