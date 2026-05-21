"""
Módulo 3 - Bot completo: detección + decisión + control de teclado
Bot dinosaurio de Google | Visión y Animación por Computadora

El bot analiza visualmente el juego y presiona teclas automáticamente:
  - ESPACIO / FLECHA ARRIBA → saltar (esquivar cactus)
  - FLECHA ABAJO            → agacharse (esquivar aves)
  - Sin acción              → camino libre

Controles:
  Q  — salir y ver reporte de métricas
  M  — alternar entre Método 1 (píxeles) y Método 2 (contornos)
  P  — pausar / reanudar el bot (el juego sigue, el bot deja de actuar)
  R  — reiniciar métricas
"""
 
import cv2
import numpy as np
import mss
import time
from pynput.keyboard import Key, Controller

# ─────────────────────────────────────────────
#  CONFIGURACIÓN CALIBRADA (CORREGIDA PARA TU PANTALLA)
# ─────────────────────────────────────────────
GAME_TOP    = 420   
GAME_LEFT   = 0
CAPTURE_W   = 800
CAPTURE_H   = 250   

ROI_LEFT    = 160   
ROI_WIDTH   = 320   
ROI_TOP     = 100   
ROI_HEIGHT  = 80    

THRESHOLD   = 127

# ── Parámetros de Control ──
PIXEL_UMBRAL      = 30
CONTORNO_AREA_MIN = 40
ALTURA_AVE        = 0.45

DISTANCIA_SALTO   = 45
DISTANCIA_AGACHAR = 55
COOLDOWN_ACCION   = 0.22

teclado = Controller()

# ─────────────────────────────────────────────
#  CAPTURA Y PREPROCESAMIENTO ADAPTATIVO
# ─────────────────────────────────────────────
def capturar_frame(sct, region):
    screenshot = sct.grab(region)
    frame = np.array(screenshot)
    return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

def preprocesar(frame):
    # Extraer ROI
    roi = frame[ROI_TOP:ROI_TOP + ROI_HEIGHT,
                ROI_LEFT:ROI_LEFT + ROI_WIDTH]

    gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # ─────────────────────────────────────────────
    #  HISTOGRAMA para determinar el modo Día/Noche
    # ─────────────────────────────────────────────
    hist = cv2.calcHist([gris], [0], None, [256], [0, 256])
    hist = hist.flatten()

    # índice del valor con mayor frecuencia (pico)
    pico = np.argmax(hist)

    # clasificación automática
    if pico > 128:
        # Fondo claro → obstáculos oscuros → invertir
        _, binaria = cv2.threshold(gris, THRESHOLD, 255, cv2.THRESH_BINARY_INV)
        modo = "Claro"
    else:
        # Fondo oscuro → obstáculos claros → no invertir
        _, binaria = cv2.threshold(gris, THRESHOLD, 255, cv2.THRESH_BINARY)
        modo = "Oscuro"

    return roi, gris, binaria, modo

# ─────────────────────────────────────────────
#  DETECCIÓN
# ─────────────────────────────────────────────
def detectar_pixeles(binaria):
    total = cv2.countNonZero(binaria)
    hay   = total > PIXEL_UMBRAL
    x_aprox = -1
    if hay:
        suma_cols = np.sum(binaria, axis=0)
        x_aprox   = int(np.argmax(suma_cols))
    return hay, total, x_aprox

def detectar_contornos(binaria):
    contornos, _ = cv2.findContours(binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contornos) == 0:
        return False, []

    # Tomar el contorno mayor
    contorno = max(contornos, key=cv2.contourArea)
    area = cv2.contourArea(contorno)

    if area < CONTORNO_AREA_MIN:
        return False, []

    # Devolvemos el recuadro del obstáculo envuelto en una lista
    x, y, w, h = cv2.boundingRect(contorno)
    return True, [(x, y, w, h)]

# ─────────────────────────────────────────────
#  CLASIFICACIÓN
# ─────────────────────────────────────────────
def clasificar(bboxes, roi_h):
    if not bboxes:
        return "ninguno", ROI_WIDTH  
    bbox = min(bboxes, key=lambda b: b[0])
    x, y, w, h = bbox
    tipo = "ave" if (y + h / 2) / roi_h < ALTURA_AVE else "cactus"
    return tipo, x

def clasificar_obstaculo(contorno):
    x, y, w, h = cv2.boundingRect(contorno)
    cx = x + w // 2
    cy = y + h // 2

    aspect_ratio = w / float(h)

    # ─────────────────────────────────────────────
    # 1) AVE — contorno horizontal
    # ─────────────────────────────────────────────
    if aspect_ratio > 1.35:
        return "ave", cx, cy, w, h

    # ─────────────────────────────────────────────
    # 2) CACTUS — contorno vertical
    # ─────────────────────────────────────────────
    if aspect_ratio < 0.75:
        return "cactus", cx, cy, w, h

    # ─────────────────────────────────────────────
    # 3) Zona ambigua → usar altura como refuerzo
    # ─────────────────────────────────────────────
    if cy < ROI_HEIGHT * ALTURA_AVE:
        return "ave", cx, cy, w, h
    else:
        return "cactus", cx, cy, w, h

# ─────────────────────────────────────────────
#  REGLA DE DECISIÓN
# ─────────────────────────────────────────────
def decidir_accion(hay_obstaculo, tipo, distancia, ultimo_tiempo_accion):
    ahora = time.time()
    if not hay_obstaculo or (ahora - ultimo_tiempo_accion < COOLDOWN_ACCION):
        return "ninguna"

    if tipo == "cactus" and distancia < DISTANCIA_SALTO:
        return "saltar"
    elif tipo == "ave" and distancia < DISTANCIA_AGACHAR:
        return "agachar"
    return "ninguna"

def ejecutar_accion(accion):
    if accion == "saltar":
        teclado.press(Key.space)
        time.sleep(0.04)
        teclado.release(Key.space)
    elif accion == "agachar":
        teclado.press(Key.down)
        time.sleep(0.25)
        teclado.release(Key.down)

# ─────────────────────────────────────────────
#  VISUALIZACIÓN Y MÉTRICAS
# ─────────────────────────────────────────────
def dibujar(frame, roi, binaria, metodo, fps, pausado, modo_juego,
            hay_obs, tipo, distancia, pixeles, bboxes, accion, metricas):

    frame_vis = frame.copy()
    color_roi = (0, 255, 0) if not hay_obs else (0, 0, 255)
    cv2.rectangle(frame_vis, (ROI_LEFT, ROI_TOP), (ROI_LEFT + ROI_WIDTH, ROI_TOP + ROI_HEIGHT), color_roi, 2)

    estado = f"OBSTACULO: {tipo.upper()}" if hay_obs else "CAMINO LIBRE"
    color_estado = (0, 0, 255) if hay_obs else (0, 200, 0)
    
    cv2.putText(frame_vis, estado, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color_estado, 2)
    cv2.putText(frame_vis, f"FPS: {fps} | MODO: {modo_juego}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 0), 2)

    metodo_txt = "Pixeles" if metodo == 1 else "Contornos"
    cv2.putText(frame_vis, f"Metodo: {metodo_txt} [M]", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    if distancia < ROI_WIDTH:
        cv2.putText(frame_vis, f"Dist: {distancia}px", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)

    cv2.putText(frame_vis, f"Accion: {accion.upper()}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128) if accion != "ninguna" else (150, 150, 150), 2)
    cv2.putText(frame_vis, f"Saltos: {metricas['saltos']} | Detec: {metricas['detecciones']}", (10, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    if pausado:
        cv2.putText(frame_vis, "[ PAUSADO ]", (10, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

    roi_vis = roi.copy()
    linea_y = int(ROI_HEIGHT * ALTURA_AVE)
    cv2.line(roi_vis, (0, linea_y), (ROI_WIDTH, linea_y), (0, 255, 255), 1)

    if metodo == 1 and hay_obs and distancia >= 0:
        cv2.line(roi_vis, (distancia, 0), (distancia, ROI_HEIGHT), (0, 0, 255), 2)
    elif metodo == 2:
        for (x, y, w, h) in bboxes:
            cv2.rectangle(roi_vis, (x, y), (x+w, y+h), (255, 0, 0), 2)

    cv2.line(roi_vis, (DISTANCIA_SALTO, 0), (DISTANCIA_SALTO, ROI_HEIGHT), (0, 255, 0), 1)
    return frame_vis, roi_vis

class Metricas:
    def __init__(self, nombre):
        self.nombre = nombre
        self.reiniciar()

    def reiniciar(self):
        self.inicio = time.time()
        self.frames = 0
        self.detecciones = 0
        self.saltos = 0
        self.agachadas = 0
        self.fps_lista = []

    def registrar(self, hay_obs, accion, fps):
        self.frames += 1
        if hay_obs: self.detecciones += 1
        if accion == "saltar": self.saltos += 1
        elif accion == "agachar": self.agachadas += 1
        self.fps_lista.append(fps)

    def reporte(self):
        elapsed = time.time() - self.inicio
        fps_prom = np.mean(self.fps_lista) if self.fps_lista else 0
        print(f"\nReporte — {self.nombre}\n{'-'*30}")
        print(f"Tiempo: {elapsed:.1f}s | Total Frames: {self.frames}")
        print(f"Detecciones: {self.detecciones} | Saltos: {self.saltos} | FPS Prom: {fps_prom:.1f}\n")

    def dict_pantalla(self):
        return {"saltos": self.saltos, "detecciones": self.detecciones}

# ─────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────
def main():
    metodo_actual   = 2  # Cambiado por defecto a Contornos (más preciso para el proyecto)
    pausado         = False
    ultimo_accion_t = 0.0

    metricas = {1: Metricas("Conteo de pixeles"), 2: Metricas("Deteccion de contornos")}
    fps_tiempo, fps_contador, fps_actual = time.time(), 0, 0

    region = {"top": GAME_TOP, "left": GAME_LEFT, "width": CAPTURE_W, "height": CAPTURE_H}

    with mss.mss() as sct:
        while True:
            frame = capturar_frame(sct, region)
            roi, gris, binaria, modo_juego = preprocesar(frame)
            if roi.size == 0:
                continue

            if metodo_actual == 1:
                hay_obs, pixeles, x_aprox = detectar_pixeles(binaria)
                bboxes = [(x_aprox, 0, 5, ROI_HEIGHT)] if hay_obs and x_aprox >= 0 else []
                tipo, distancia = clasificar(bboxes, ROI_HEIGHT)
            else:
                hay_obs, bboxes = detectar_contornos(binaria)
                tipo, distancia = clasificar(bboxes, ROI_HEIGHT) 
                pixeles = cv2.countNonZero(binaria)

            accion = "ninguna"
            if not pausado:
                accion = decidir_accion(hay_obs, tipo, distancia, ultimo_accion_t)
                if accion != "ninguna":
                    ejecutar_accion(accion)
                    ultimo_accion_t = time.time()

            fps_contador += 1
            ahora = time.time()
            if ahora - fps_tiempo >= 1.0:
                fps_actual, fps_contador, fps_tiempo = fps_contador, 0, ahora

            metricas[metodo_actual].registrar(hay_obs, accion, fps_actual)

            frame_vis, roi_vis = dibujar(
                frame, roi, binaria, metodo_actual, fps_actual, pausado, modo_juego,
                hay_obs, tipo, distancia, pixeles, bboxes, accion, metricas[metodo_actual].dict_pantalla()
            )
            
            cv2.imshow("Bot Dinosaurio", frame_vis)
            cv2.imshow("ROI binarizada", binaria)
            cv2.imshow("ROI + marcadores", roi_vis)

            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord('q'):
                break
            elif tecla == ord('m'):
                metodo_actual = 2 if metodo_actual == 1 else 1
            elif tecla == ord('p'):
                pausado = not pausado
            elif tecla == ord('r'):
                metricas[metodo_actual].reiniciar()

    for m in metricas.values():
        if m.frames > 0: m.reporte()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()