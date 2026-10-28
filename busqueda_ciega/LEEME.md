# Simulador de Búsqueda Ciega (BFS / DFS) – Caso Práctico: Laberinto

Versión en Python (tkinter) del simulador HTML.

## Ejecutar
    python laberinto_busqueda_ciega.py

Requiere Python 3.8+ con tkinter (viene incluido en Windows/macOS).
En Linux: `sudo apt install python3-tk`

## Contenido
- `laberinto_busqueda_ciega.py` – simulador con interfaz (diagrama de flujo, cuadrícula, controles, guía de colores).
- `test_motor.py` – prueba del algoritmo sin interfaz (verifica la traza del apunte).

## Uso
- Laberinto: "Caso práctico 5x5 (apunte)" o "Aleatorio 15x15".
- Estrategia: BFS (cola FIFO) o DFS (pila LIFO).
- "Auto" corre continuo (velocidad 5–1000 ms); "Decisión" avanza una decisión del diagrama de flujo.
- Orden de operadores: Este, Sur, Oeste, Norte. La flecha apunta al nodo padre.
