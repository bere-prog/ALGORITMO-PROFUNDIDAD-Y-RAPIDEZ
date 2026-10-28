#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulador Didáctico de Búsqueda Ciega (BFS / DFS) - Caso Práctico: Laberinto
Interfaz tkinter (solo librería estándar de Python 3.8+).

Orden de operadores (según el apunte): 1. Este, 2. Sur, 3. Oeste, 4. Norte
La flecha de cada celda amarilla/morada apunta hacia su nodo PADRE.
"""
import random
import tkinter as tk
from tkinter import ttk

# ───────────────────────── Paleta ─────────────────────────
BG, PANEL, BORDER, TEXT, ACCENT = "#070b14", "#111827", "#1f293d", "#f8fafc", "#38bdf8"
C_START, C_GOAL, C_WALL, C_EMPTY = "#22c55e", "#ef4444", "#1e293b", "#0b1120"
C_FRONTIER, C_VISITED, C_CURRENT = "#eab308", "#4f46e5", "#ec4899"
C_TESTING, C_PATH = "#f97316", "#10b981"

# Caso práctico del apunte (5x5). S=inicio (0,0), G=meta (4,4), #=muro
CASE_MAZE = [
    "S.#..",
    "#.#.#",
    ".....",
    ".###.",
    "...#G",
]

# Orden estándar: Este, Sur, Oeste, Norte  ->  (nombre, dx, dy, flecha hacia el padre)
MOVES = [("Este", 1, 0, "←"), ("Sur", 0, 1, "↑"), ("Oeste", -1, 0, "→"), ("Norte", 0, -1, "↓")]

# Estados de la máquina de decisiones
ST_EMPTY, ST_POP, ST_GOAL, ST_EXPAND, ST_TEST, ST_ENQ, ST_END = range(1, 8)


# ───────────────────────── Laberintos ─────────────────────────
def maze_from_text(rows):
    """Devuelve (walls[y][x], start, goal) a partir del dibujo de texto."""
    walls, start, goal = [], None, None
    for y, row in enumerate(rows):
        walls.append([ch == "#" for ch in row])
        for x, ch in enumerate(row):
            if ch == "S":
                start = (x, y)
            elif ch == "G":
                goal = (x, y)
    return walls, start, goal


def random_maze(size=15):
    """Laberinto perfecto (backtracker) + algunos huecos extra, como en el HTML."""
    walls = [[True] * size for _ in range(size)]
    walls[1][1] = False
    stack = [(1, 1)]
    dirs = [(0, -2), (0, 2), (-2, 0), (2, 0)]
    while stack:
        cx, cy = stack[-1]
        opts = []
        for dx, dy in dirs:
            nx, ny = cx + dx, cy + dy
            if 0 < nx < size - 1 and 0 < ny < size - 1 and walls[ny][nx]:
                opts.append((nx, ny, cx + dx // 2, cy + dy // 2))
        if opts:
            nx, ny, wx, wy = random.choice(opts)
            walls[wy][wx] = False
            walls[ny][nx] = False
            stack.append((nx, ny))
        else:
            stack.pop()
    for _ in range(8):
        walls[random.randint(1, size - 2)][random.randint(1, size - 2)] = False
    start, goal = (1, 1), (size - 2, size - 2)
    walls[1][1] = walls[size - 2][size - 2] = False
    return walls, start, goal


# ───────────────────────── Motor de búsqueda ─────────────────────────
class SearchEngine:
    """Máquina de estados: cada step() es UNA decisión del diagrama de flujo."""

    def __init__(self, walls, start, goal, algo="BFS"):
        self.walls, self.start, self.goal, self.algo = walls, start, goal, algo
        self.h, self.w = len(walls), len(walls[0])
        self.reset()

    def reset(self):
        self.frontier = [self.start]
        self.visited = {self.start}          # descubiertos (frontera + cerrados)
        self.closed = set()                  # explorados por completo (morado)
        self.parent = {self.start: None}
        self.arrow = {}
        self.g = {self.start: 0}
        self.current = None
        self.testing = None
        self.neighbors = []
        self.idx = 0
        self.path = []
        self.finished = False
        self.success = False
        self.state = ST_EMPTY
        self.expanded = 0
        self.generated = 1
        self.order = []                      # orden de expansión (traza)

    def in_bounds(self, p):
        return 0 <= p[0] < self.w and 0 <= p[1] < self.h

    def step(self):
        """Ejecuta una decisión. Devuelve (id_nodo_flujo, mensaje, etiqueta)."""
        if self.finished:
            return "path", "La búsqueda ya terminó.", "FIN"

        if self.state == ST_EMPTY:
            if not self.frontier:
                self.finished = True
                return "empty", "Frontera vacía: no existe solución.", "FALLO"
            self.state = ST_POP
            return ("empty",
                    f"Paso 2: ¿Frontera vacía? NO ({len(self.frontier)} pendientes). Se extrae el siguiente nodo.",
                    "DECISIÓN")

        if self.state == ST_POP:
            self.testing = None
            self.current = self.frontier.pop(0) if self.algo == "BFS" else self.frontier.pop()
            self.state = ST_GOAL
            estruct = "Cola FIFO (el más antiguo)" if self.algo == "BFS" else "Pila LIFO (el último insertado)"
            return ("pop",
                    f"Paso 3: Se extrae {self.current} de la {estruct} → nodo activo (rosa).",
                    "ACTIVO")

        if self.state == ST_GOAL:
            if self.current == self.goal:
                self.path = self._reconstruct()
                self.finished = self.success = True
                self.state = ST_END
                return ("path",
                        f"Paso 4: ¡Meta {self.goal} encontrada! Ruta con {len(self.path) - 1} pasos "
                        f"({len(self.path)} estados).",
                        "ÉXITO")
            self.state = ST_EXPAND
            return ("goal", f"Paso 4: ¿{self.current} es Meta? NO. Se expanden sus vecinos.", "DECISIÓN")

        if self.state == ST_EXPAND:
            cx, cy = self.current
            self.neighbors = [((cx + dx, cy + dy), name, arrow) for name, dx, dy, arrow in MOVES]
            self.idx = 0
            self.state = ST_TEST
            return ("expand",
                    f"Paso 5: Se generan 4 sucesores de {self.current} en orden Este, Sur, Oeste, Norte.",
                    "EXPANSIÓN")

        if self.state == ST_TEST:
            if self.idx >= len(self.neighbors):
                self.testing = None
                self.closed.add(self.current)
                self.expanded += 1
                self.order.append(self.current)
                self.state = ST_EMPTY
                return ("filter", f"Vecinos de {self.current} completados → pasa a Explorado (morado).", "CERRADO")
            pos, name, _ = self.neighbors[self.idx]
            ok_bounds = self.in_bounds(pos)
            is_wall = ok_bounds and self.walls[pos[1]][pos[0]]
            self.testing = pos if ok_bounds and not is_wall else None
            if not ok_bounds or is_wall or pos in self.visited:
                reason = "fuera de límites" if not ok_bounds else ("muro" if is_wall else "ya visitado")
                self.idx += 1
                return ("filter", f"Paso 6: Vecino {name} {pos}: ✘ DESCARTADO ({reason}).", "FILTRADO")
            self.state = ST_ENQ
            return ("filter", f"Paso 6: Vecino {name} {pos}: ✔ VÁLIDO (libre y no visitado).", "APROBADO")

        if self.state == ST_ENQ:
            pos, name, arrow = self.neighbors[self.idx]
            self.visited.add(pos)
            self.parent[pos] = self.current
            self.arrow[pos] = arrow
            self.g[pos] = self.g[self.current] + 1
            self.frontier.append(pos)
            self.generated += 1
            self.testing = None
            self.idx += 1
            self.state = ST_TEST
            return ("enqueue",
                    f"Paso 7: {pos}.parent = {self.current}, vector {arrow}. Entra a la Frontera (g={self.g[pos]}).",
                    "ENCOLADO")

    def _reconstruct(self):
        p, out = self.goal, []
        while p is not None:
            out.append(p)
            p = self.parent[p]
        return out[::-1]


# ───────────────────────── Interfaz ─────────────────────────
FLOW_STEPS = [
    ("start",   "1. INICIO",               "Inicializar Frontera con s₀",          False),
    ("empty",   "2. ¿FRONTERA VACÍA?",     "¿Quedan nodos pendientes?",            True),
    ("pop",     "3. EXTRAER NODO (n)",     "FIFO (Cola) en BFS | LIFO (Pila) en DFS", False),
    ("goal",    "4. ¿ES META? (n == G)",   "¿Coordenadas coinciden con la meta?",  True),
    ("expand",  "5. GENERAR SUCESOR",      "Seleccionar vecino (E, S, O, N)",      False),
    ("filter",  "6. FILTRAR OBSTÁCULOS",   "¿Libre de muro y NO visitado?",        True),
    ("enqueue", "7. ASIGNAR PADRE Y ENCOLAR", "child.parent = n, vector y frontera", False),
    ("path",    "8. RECONSTRUCCIÓN (ÉXITO)", "Seguir punteros padre hacia atrás",  False),
]

COLOR_GUIDE = [
    (C_START, "Verde: Inicio s₀."),
    (C_GOAL, "Rojo: Meta objetivo G."),
    (C_WALL, "Gris Pizarra: Muro infranqueable (#)."),
    (C_CURRENT, "Rosa/Magenta: Nodo Activo evaluado ahora."),
    (C_TESTING, "Naranja: Vecino en prueba de filtros."),
    (C_FRONTIER, "Amarillo: Frontera (flecha hacia el padre)."),
    (C_VISITED, "Morado: Explorados (cerrados totalmente)."),
    (C_PATH, "Esmeralda: Ruta final hacia la meta."),
]

CANVAS_PX = 450


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador de Búsqueda Ciega – Caso Práctico: Resolución del Laberinto")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.running = False
        self.after_id = None
        self.flow_widgets = {}
        self.paso = 0

        self._build_header()
        main = tk.Frame(self, bg=BG)
        main.pack(padx=12, pady=(0, 12))
        self._build_flow(main)
        self._build_grid(main)
        self._build_controls(main)
        self.load_maze()

    # ---------- construcción ----------
    def _build_header(self):
        tk.Label(self, text="Simulador Didáctico de Decisiones – Laberinto", bg=BG, fg=ACCENT,
                 font=("Segoe UI", 15, "bold")).pack(pady=(10, 0))
        tk.Label(self, text="Inspección de Estados en Vivo para Clases de Algoritmos de Búsqueda",
                 bg=BG, fg="#94a3b8", font=("Segoe UI", 9)).pack()
        ban = tk.Frame(self, bg="#0d1829", highlightbackground=ACCENT, highlightthickness=1)
        ban.pack(fill="x", padx=12, pady=8)
        self.banner_msg = tk.Label(ban, text="", bg="#0d1829", fg="#e2e8f0", font=("Segoe UI", 10),
                                   anchor="w", justify="left", wraplength=1050)
        self.banner_msg.pack(side="left", padx=10, pady=6, fill="x", expand=True)
        self.banner_tag = tk.Label(ban, text="LISTO", bg=ACCENT, fg="#04101e", font=("Segoe UI", 9, "bold"),
                                   padx=8, pady=2)
        self.banner_tag.pack(side="right", padx=10)

    def _build_flow(self, parent):
        box = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        box.pack(side="left", anchor="n", padx=7)
        tk.Label(box, text="DIAGRAMA DE FLUJO", bg=PANEL, fg=ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(pady=(8, 4))
        for i, (key, title, sub, decision) in enumerate(FLOW_STEPS):
            f = tk.Frame(box, bg="#0d1527" if decision else "#090e1a",
                         highlightbackground="#334155", highlightthickness=2, width=270)
            f.pack(padx=10, pady=1, fill="x")
            t = tk.Label(f, text=title, bg=f["bg"], fg=TEXT, font=("Segoe UI", 9, "bold"), anchor="w")
            s = tk.Label(f, text=sub, bg=f["bg"], fg="#94a3b8", font=("Segoe UI", 8), anchor="w")
            t.pack(fill="x", padx=6, pady=(3, 0))
            s.pack(fill="x", padx=6, pady=(0, 3))
            self.flow_widgets[key] = (f, t, s)
            if i < len(FLOW_STEPS) - 1:
                tk.Label(box, text="▼", bg=PANEL, fg="#475569", font=("Segoe UI", 7)).pack()
        tk.Label(box, text="", bg=PANEL).pack(pady=2)

    def _build_grid(self, parent):
        box = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=2)
        box.pack(side="left", anchor="n", padx=7)
        self.canvas = tk.Canvas(box, width=CANVAS_PX, height=CANVAS_PX, bg="#1f293d", highlightthickness=0)
        self.canvas.pack(padx=8, pady=8)
        self.lbl_info = tk.Label(box, text="", bg=PANEL, fg="#94a3b8", font=("Consolas", 9))
        self.lbl_info.pack(pady=(0, 6))

    def _card(self, parent):
        c = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        c.pack(fill="x", pady=4)
        return c

    def _build_controls(self, parent):
        col = tk.Frame(parent, bg=BG, width=300)
        col.pack(side="left", anchor="n", padx=7)

        c = self._card(col)
        tk.Label(c, text="Laberinto", bg=PANEL, fg="#94a3b8", font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(8, 0))
        self.maze_var = tk.StringVar(value="Caso práctico 5×5 (apunte)")
        cb1 = ttk.Combobox(c, textvariable=self.maze_var, state="readonly", width=34,
                           values=["Caso práctico 5×5 (apunte)", "Aleatorio 15×15"])
        cb1.pack(padx=10, pady=2)
        cb1.bind("<<ComboboxSelected>>", lambda e: self.load_maze())

        tk.Label(c, text="Estrategia", bg=PANEL, fg="#94a3b8", font=("Segoe UI", 9)).pack(anchor="w", padx=10)
        self.algo_var = tk.StringVar(value="BFS (Anchura - Cola FIFO)")
        cb2 = ttk.Combobox(c, textvariable=self.algo_var, state="readonly", width=34,
                           values=["BFS (Anchura - Cola FIFO)", "DFS (Profundidad - Pila LIFO)"])
        cb2.pack(padx=10, pady=2)
        cb2.bind("<<ComboboxSelected>>", lambda e: self.reset_search())

        self.speed_lbl = tk.Label(c, text="Velocidad: 300 ms", bg=PANEL, fg=ACCENT, font=("Segoe UI", 9, "bold"))
        self.speed_lbl.pack(anchor="w", padx=10, pady=(6, 0))
        self.speed = tk.Scale(c, from_=5, to=1000, orient="horizontal", resolution=5, showvalue=False,
                              bg=PANEL, fg=TEXT, troughcolor="#090e1a", highlightthickness=0, length=270,
                              command=lambda v: self.speed_lbl.config(text=f"Velocidad: {v} ms"))
        self.speed.set(300)
        self.speed.pack(padx=10)

        r1 = tk.Frame(c, bg=PANEL); r1.pack(fill="x", padx=10, pady=(4, 2))
        self.btn_auto = tk.Button(r1, text="▶ Auto", bg="#0284c7", fg="white", bd=0, font=("Segoe UI", 9, "bold"),
                                  command=self.toggle_auto)
        self.btn_auto.pack(side="left", expand=True, fill="x", padx=(0, 3))
        self.btn_step = tk.Button(r1, text="Decisión ⏭", bg="#6366f1", fg="white", bd=0,
                                  font=("Segoe UI", 9, "bold"), command=self.manual_step)
        self.btn_step.pack(side="left", expand=True, fill="x", padx=(3, 0))
        r2 = tk.Frame(c, bg=PANEL); r2.pack(fill="x", padx=10, pady=(2, 8))
        tk.Button(r2, text="↻ Laberinto", bg="#090e1a", fg="white", bd=0, command=self.new_maze
                  ).pack(side="left", expand=True, fill="x", padx=(0, 3))
        tk.Button(r2, text="Limpiar", bg="#090e1a", fg="white", bd=0, command=self.reset_search
                  ).pack(side="left", expand=True, fill="x", padx=(3, 0))

        g = self._card(col)
        tk.Label(g, text="SIGNIFICADO DE LOS COLORES", bg=PANEL, fg=ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 3))
        for color, txt in COLOR_GUIDE:
            row = tk.Frame(g, bg="#0a0f1d"); row.pack(fill="x", padx=10, pady=1)
            tk.Frame(row, bg=color, width=14, height=14).pack(side="left", padx=4, pady=2)
            tk.Label(row, text=txt, bg="#0a0f1d", fg="#e2e8f0", font=("Segoe UI", 8)).pack(side="left")
        tk.Label(g, text="", bg=PANEL).pack(pady=1)

        t = self._card(col)
        self.telemetry = tk.Label(t, text="", bg=PANEL, fg="#cbd5e1", font=("Consolas", 9), justify="left", anchor="w")
        self.telemetry.pack(padx=10, pady=8, fill="x")

    # ---------- lógica de control ----------
    def algo(self):
        return "BFS" if self.algo_var.get().startswith("BFS") else "DFS"

    def load_maze(self):
        self.stop_auto()
        if self.maze_var.get().startswith("Caso"):
            self.maze = maze_from_text(CASE_MAZE)
        else:
            self.maze = random_maze(15)
        self.reset_search()

    def new_maze(self):
        if self.maze_var.get().startswith("Caso"):
            self.maze_var.set("Aleatorio 15×15")
        self.load_maze()

    def reset_search(self):
        self.stop_auto()
        walls, start, goal = self.maze
        self.engine = SearchEngine(walls, start, goal, self.algo())
        self.paso = 0
        self.btn_auto.config(state="normal")
        self.btn_step.config(state="normal")
        self.highlight("start")
        self.set_banner(f"Listo. Estrategia {self.algo()}. Presiona '▶ Auto' o 'Decisión ⏭'.", "INICIO")
        self.lbl_info.config(text=f"Inicio S={start}   Meta G={goal}   Orden: Este, Sur, Oeste, Norte")
        self.redraw()
        self.update_telemetry()

    def do_step(self):
        key, msg, tag = self.engine.step()
        self.paso += 1
        self.highlight(key, success=(tag == "ÉXITO"))
        self.set_banner(msg, tag)
        self.redraw()
        self.update_telemetry()
        if self.engine.finished:
            self.stop_auto()
            self.btn_auto.config(state="disabled")
            self.btn_step.config(state="disabled")

    def manual_step(self):
        if not self.running:
            self.do_step()

    def toggle_auto(self):
        if self.running:
            self.stop_auto()
        else:
            self.running = True
            self.btn_auto.config(text="⏸ Pausar")
            self.btn_step.config(state="disabled")
            self.loop()

    def loop(self):
        if not self.running or self.engine.finished:
            return
        self.do_step()
        if self.running:
            self.after_id = self.after(int(self.speed.get()), self.loop)

    def stop_auto(self):
        self.running = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.btn_auto.config(text="▶ Auto")
        if hasattr(self, "engine") and not self.engine.finished:
            self.btn_step.config(state="normal")

    # ---------- dibujo ----------
    def set_banner(self, text, tag):
        self.banner_msg.config(text=text)
        self.banner_tag.config(text=tag)

    def highlight(self, key, success=False):
        for k, (f, t, s) in self.flow_widgets.items():
            base = "#0d1527" if dict((a, d) for a, _, _, d in FLOW_STEPS)[k] else "#090e1a"
            f.config(bg=base, highlightbackground="#334155")
            t.config(bg=base, fg=TEXT); s.config(bg=base, fg="#94a3b8")
        f, t, s = self.flow_widgets[key]
        bg = "#064e3b" if success else "#0c2d48"
        f.config(bg=bg, highlightbackground=C_PATH if success else ACCENT)
        t.config(bg=bg); s.config(bg=bg, fg="white")

    def redraw(self):
        e = self.engine
        n = e.w
        cell = CANVAS_PX // n
        gap = 2
        fsz = max(8, int(cell * (0.30 if n <= 7 else 0.38)))
        self.canvas.delete("all")
        front, path = set(e.frontier), set(e.path)
        for y in range(e.h):
            for x in range(e.w):
                p = (x, y)
                if p == e.start:   fill, txt = C_START, "S"
                elif p == e.goal:  fill, txt = C_GOAL, "G"
                elif e.walls[y][x]: fill, txt = C_WALL, ""
                else:
                    txt = e.arrow.get(p, "")
                    if p in path:            fill = C_PATH
                    elif p == e.current:     fill = C_CURRENT
                    elif p == e.testing:     fill = C_TESTING
                    elif p in e.closed:      fill = C_VISITED
                    elif p in front:         fill = C_FRONTIER
                    else:                    fill = C_EMPTY
                # en la meta/inicio, el actual se resalta con borde
                x0, y0 = x * cell + gap, y * cell + gap
                outline = C_CURRENT if (p == e.current and p in (e.start, e.goal)) else ""
                self.canvas.create_rectangle(x0, y0, x0 + cell - gap, y0 + cell - gap, fill=fill,
                                             outline=outline, width=3 if outline else 0)
                if txt:
                    fg = "#022c22" if p == e.start else ("black" if fill == C_FRONTIER else "white")
                    self.canvas.create_text(x0 + (cell - gap) / 2, y0 + (cell - gap) / 2, text=txt, fill=fg,
                                            font=("Segoe UI", fsz, "bold"))
                if n <= 7 and not e.walls[y][x]:  # coordenada pequeña en el caso 5x5
                    self.canvas.create_text(x0 + 4, y0 + 3, anchor="nw", text=f"{x},{y}", fill="#94a3b8",
                                            font=("Consolas", 7))

    def update_telemetry(self):
        e = self.engine
        node = e.current or e.start
        dx, dy = abs(node[0] - e.goal[0]), abs(node[1] - e.goal[1])
        self.telemetry.config(text=(
            f"Nodo: {node}   g(n): {e.g.get(node, 0)} pasos\n"
            f"Manhattan (L1): {dx + dy}   Euclidiana (L2): {(dx*dx + dy*dy) ** 0.5:.3f}\n"
            f"Chebyshev (L∞): {max(dx, dy)}\n"
            f"Frontera: {len(e.frontier)} pendientes\n"
            f"Expandidos: {e.expanded}   Generados: {e.generated}\n"
            f"Decisiones ejecutadas: {self.paso}"
        ))


if __name__ == "__main__":
    App().mainloop()
