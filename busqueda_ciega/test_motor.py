from laberinto_busqueda_ciega import *
w,s,g = maze_from_text(CASE_MAZE)
for a in ("BFS","DFS"):
    e = SearchEngine(w,s,g,a)
    while not e.finished: e.step()
    print(a, e.success, len(e.path)-1, "pasos | expandidos:", e.expanded)
    print(" ruta:", e.path)
    print(" orden:", e.order)
