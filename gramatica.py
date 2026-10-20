# Clase para guardar una gramatica libre de contexto y funciones para leerla
# desde un archivo de texto.
#
# Formato del archivo (igual que el del profe):
#   A -> B C | a | e
# - Lo que esta a la izquierda de -> es una variable (no terminal).
# - Cualquier simbolo que nunca aparece a la izquierda es terminal.
# - Los simbolos se separan con espacios.
# - 'e' (o 'ε') significa epsilon (cadena vacia).
# - Las lineas que empiezan con # son comentarios.
# - La variable inicial es la de la primera linea.

EPSILON = ("e", "ε", "epsilon")


class Gramatica:
    # Guarda la variable inicial y las producciones.
    # Ejemplo: NP -> Det N | he | she  queda como
    #   {"NP": [("Det", "N"), ("he",), ("she",)]}
    # Los lados derechos son tuplas para poder usarlos como llaves en cyk.py.

    def __init__(self, inicial, producciones):
        self.inicial = inicial
        # diccionario: variable -> lista de tuplas (cada tupla es un lado derecho)
        # la tupla vacia () es epsilon
        self.producciones = producciones

    def variables(self):
        return list(self.producciones.keys())

    def es_variable(self, simbolo):
        # es variable si tiene producciones propias, si no es terminal
        return simbolo in self.producciones

    def terminales(self):
        # junta todos los simbolos que no son variables, sin repetir
        ts = []
        for cuerpos in self.producciones.values():
            for cuerpo in cuerpos:
                for s in cuerpo:
                    if not self.es_variable(s) and s not in ts:
                        ts.append(s)
        return ts

    def copia(self):
        prods = {}
        for var, cuerpos in self.producciones.items():
            prods[var] = list(cuerpos)
        return Gramatica(self.inicial, prods)

    def agregar(self, var, cuerpo):
        # agrega la produccion si no existe ya
        if var not in self.producciones:
            self.producciones[var] = []
        if cuerpo not in self.producciones[var]:
            self.producciones[var].append(cuerpo)

    def num_producciones(self):
        return sum(len(c) for c in self.producciones.values())

    def __str__(self):
        # texto con el mismo formato del archivo (A -> B C | a)
        lineas = []
        # la inicial siempre de primero
        orden = [self.inicial] + [v for v in self.producciones if v != self.inicial]
        for var in orden:
            cuerpos = self.producciones.get(var, [])
            if not cuerpos:
                continue
            textos = []
            for c in cuerpos:
                if len(c) == 0:
                    textos.append("e")
                else:
                    textos.append(" ".join(c))
            lineas.append(var + " -> " + " | ".join(textos))
        return "\n".join(lineas)


def leer_gramatica(ruta):
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    return leer_gramatica_texto(texto)


def leer_gramatica_texto(texto):
    # Se lee en dos pasadas: en la primera se sacan todas las variables (lado
    # izquierdo) y en la segunda se arman las producciones. Asi ya se sabe que
    # es variable aunque se use antes de definirse.
    inicial = None
    prods = {}
    lineas = []
    for num, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.strip()
        if linea == "" or linea.startswith("#"):
            continue
        if "->" not in linea:
            raise ValueError("Linea %d mal escrita (falta '->'): %s" % (num, linea))
        izq, der = linea.split("->", 1)
        izq = izq.strip()
        if izq == "" or " " in izq:
            raise ValueError("Linea %d: el lado izquierdo debe ser una sola variable" % num)
        if inicial is None:
            inicial = izq
        if izq not in prods:
            prods[izq] = []
        lineas.append((izq, der))

    # se hace en otra pasada para ya saber todas las variables
    for izq, der in lineas:
        for alternativa in der.split("|"):
            simbolos = alternativa.split()
            if len(simbolos) == 0 or (len(simbolos) == 1 and simbolos[0] in EPSILON):
                cuerpo = ()
            else:
                # si hay una 'e' en medio de otros simbolos la ignoramos (A -> e B = A -> B)
                cuerpo = tuple(s for s in simbolos if s not in EPSILON)
            if cuerpo not in prods[izq]:
                prods[izq].append(cuerpo)

    if inicial is None:
        raise ValueError("La gramatica esta vacia")
    return Gramatica(inicial, prods)


def guardar_gramatica(g, ruta):
    # se usa para guardar la version en CNF (ej. gramaticas/1-cnf.txt)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(str(g) + "\n")
