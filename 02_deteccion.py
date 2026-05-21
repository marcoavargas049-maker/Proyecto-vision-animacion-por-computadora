"""
Módulo 2 - Detección de obstáculos, clasificación y métricas
Bot dinosaurio de Google | Visión y Animación por Computadora

Métodos implementados:
  Método 1 — Conteo de píxeles: cuenta píxeles blancos en la ROI binarizada.
             Si superan un umbral, hay obstáculo.
  Método 2 — Detección de contornos: usa cv2.findContours para encontrar
             formas en la ROI y filtra por tamaño mínimo.

Controles:
  Q  — salir
  M  — alternar entre Método 1 y Método 2
  C  — modo calibración
"""

import cv2
import numpy as np
import mss
import time

# ─────────────────────────────────────────────
#  CONFIGURACIÓN (valores calibrados)
# ─────────────────────────────────────────────
GAME_TOP    = 530
GAME_LEFT   = 0
CAPTURE_W   = 800
CAPTURE_H   = 200

ROI_LEFT    = 150
ROI_WIDTH   = 400
ROI_TOP     = 40
ROI_HEIGHT  = 100

THRESHOLD   = 127

# ── Método 1: conteo de píxeles ──
PIXEL_UMBRAL = 80      # mínimo de píxeles blancos para considerar obstáculo

# ── Método 2: contornos ──
CONTORNO_AREA_MIN = 50  # área mínima de contorno para filtrar ruido

# ── Clasificación ──
# Si el centroide del obstáculo está en la mitad superior del ROI → ave
# Si está en la mitad inferior → cactus
ALTURA_AVE = 0.45       # fracción del alto del ROI; arriba de esto = ave


# ─────────────────────────────────────────────
#  CAPTURA Y PREPROCESAMIENTO
# ─────────────────────────────────────────────
def capturar_frame(sct, region):
    screenshot = sct.grab(region)
    frame = np.array(screenshot)
    return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)


def preprocesar(frame):
    """Extrae ROI, convierte a gris y binariza."""
    roi = frame[ROI_TOP:ROI_TOP + ROI_HEIGHT,
                ROI_LEFT:ROI_LEFT + ROI_WIDTH]
    gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, binaria = cv2.threshold(gris, THRESHOLD, 255, cv2.THRESH_BINARY_INV)
    return roi, gris, binaria


# ─────────────────────────────────────────────
#  MÉTODO 1: CONTEO DE PÍXELES
# ─────────────────────────────────────────────
def detectar_pixeles(binaria):
    """
    Cuenta píxeles blancos en la ROI binarizada.
    Retorna: (hay_obstaculo, cantidad_pixeles, x_aproximada)
    """
    total_blancos = cv2.countNonZero(binaria)
    hay_obstaculo = total_blancos > PIXEL_UMBRAL

    # Estimar posición horizontal: columna con más píxeles blancos
    x_aprox = -1
    if hay_obstaculo:
        suma_cols = np.sum(binaria, axis=0)
        x_aprox = int(np.argmax(suma_cols))

    return hay_obstaculo, total_blancos, x_aprox


# ─────────────────────────────────────────────
#  MÉTODO 2: DETECCIÓN DE CONTORNOS
# ─────────────────────────────────────────────
def detectar_contornos(binaria):
    """
    Encuentra contornos en la ROI binarizada y filtra por área mínima.
    Retorna: (hay_obstaculo, contornos_validos, bounding_boxes)
    """
    contornos, _ = cv2.findContours(
        binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    validos = []
    bboxes  = []
    for cnt in contornos:
        area = cv2.contourArea(cnt)
        if area >= CONTORNO_AREA_MIN:
            validos.append(cnt)
            x, y, w, h = cv2.boundingRect(cnt)
            bboxes.append((x, y, w, h))

    hay_obstaculo = len(validos) > 0
    return hay_obstaculo, validos, bboxes


# ─────────────────────────────────────────────
#  CLASIFICACIÓN: CACTUS O AVE
# ─────────────────────────────────────────────
def clasificar_obstaculo(bboxes, roi_h):
    """
    Clasifica el obstáculo más cercano (más a la izquierda del ROI).
    Un obstáculo en la mitad superior → ave; en la inferior → cactus.
    Retorna: ('cactus'|'ave'|'desconocido', distancia_x)
    """
    if not bboxes:
        return "ninguno", -1

    # El más cercano es el de menor x
    bbox_cercano = min(bboxes, key=lambda b: b[0])
    x, y, w, h   = bbox_cercano
    centro_y      = y + h / 2
    distancia_x   = x  # píxeles desde el borde izquierdo del ROI

    if centro_y / roi_h < ALTURA_AVE:
        tipo = "ave"
    else:
        tipo = "cactus"

    return tipo, distancia_x


# ─────────────────────────────────────────────
#  VISUALIZACIÓN
# ─────────────────────────────────────────────
def dibujar_info(frame, roi_vis, binaria, metodo, fps,
                 hay_obstaculo, tipo, distancia, pixeles, bboxes):
    """Dibuja toda la información de detección sobre los frames."""

    # ── Frame principal ──
    frame_vis = frame.copy()
    cv2.rectangle(frame_vis,
                  (ROI_LEFT, ROI_TOP),
                  (ROI_LEFT + ROI_WIDTH, ROI_TOP + ROI_HEIGHT),
                  (0, 255, 0), 2)

    color_alerta = (0, 0, 255) if hay_obstaculo else (0, 255, 0)
    estado_txt   = f"OBSTACULO: {tipo.upper()}" if hay_obstaculo else "CAMINO LIBRE"
    cv2.putText(frame_vis, estado_txt, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_alerta, 2)
    cv2.putText(frame_vis, f"FPS: {fps}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
    cv2.putText(frame_vis, f"Metodo: {'Pixeles' if metodo == 1 else 'Contornos'} [M para cambiar]",
                (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    if distancia >= 0:
        cv2.putText(frame_vis, f"Distancia: {distancia}px", (10, 115),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1)

    # ── ROI con detecciones dibujadas ──
    roi_vis2 = roi_vis.copy()

    if metodo == 1 and hay_obstaculo:
        # Marcar columna de mayor densidad
        suma_cols = np.sum(binaria, axis=0)
        x_max = int(np.argmax(suma_cols))
        cv2.line(roi_vis2, (x_max, 0), (x_max, ROI_HEIGHT), (0, 0, 255), 2)
        cv2.putText(roi_vis2, f"px:{pixeles}", (5, 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

    elif metodo == 2:
        for (x, y, w, h) in bboxes:
            cv2.rectangle(roi_vis2, (x, y), (x + w, y + h), (255, 0, 0), 2)
        if hay_obstaculo:
            cv2.putText(roi_vis2, f"{tipo}", (5, 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)

    # Línea divisoria ave/cactus (referencia visual)
    linea_y = int(ROI_HEIGHT * ALTURA_AVE)
    cv2.line(roi_vis2, (0, linea_y), (ROI_WIDTH, linea_y), (0, 255, 255), 1)
    cv2.putText(roi_vis2, "ave", (ROI_WIDTH - 35, linea_y - 3),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
    cv2.putText(roi_vis2, "cactus", (ROI_WIDTH - 55, linea_y + 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)

    return frame_vis, roi_vis2


# ─────────────────────────────────────────────
#  MÉTRICAS
# ─────────────────────────────────────────────
class Metricas:
    def __init__(self, nombre_metodo):
        self.nombre       = nombre_metodo
        self.frames       = 0
        self.detecciones  = 0
        self.fps_lista    = []
        self.inicio       = time.time()

    def registrar(self, hay_obstaculo, fps):
        self.frames += 1
        if hay_obstaculo:
            self.detecciones += 1
        self.fps_lista.append(fps)

    def reporte(self):
        elapsed  = time.time() - self.inicio
        fps_prom = np.mean(self.fps_lista) if self.fps_lista else 0
        print(f"\n{'='*40}")
        print(f"  Métricas — {self.nombre}")
        print(f"{'='*40}")
        print(f"  Tiempo activo : {elapsed:.1f}s")
        print(f"  Frames totales: {self.frames}")
        print(f"  Detecciones   : {self.detecciones}")
        print(f"  FPS promedio  : {fps_prom:.1f}")
        print(f"{'='*40}\n")


# ─────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  Bot Dinosaurio | Módulo 2: Detección")
    print("=" * 50)
    print("Controles: Q = salir | M = cambiar método\n")

    metodo_actual = 1   # 1 = píxeles, 2 = contornos
    metricas = {
        1: Metricas("Conteo de pixeles"),
        2: Metricas("Deteccion de contornos"),
    }

    fps_tiempo   = time.time()
    fps_contador = 0
    fps_actual   = 0

    region = {
        "top": GAME_TOP, "left": GAME_LEFT,
        "width": CAPTURE_W, "height": CAPTURE_H,
    }

    with mss.mss() as sct:
        while True:
            frame  = capturar_frame(sct, region)
            roi, gris, binaria = preprocesar(frame)

            if roi.size == 0:
                continue

            # ── Detección según método activo ──
            if metodo_actual == 1:
                hay_obs, pixeles, x_aprox = detectar_pixeles(binaria)
                bboxes  = [(x_aprox, 0, 5, ROI_HEIGHT)] if hay_obs and x_aprox >= 0 else []
                tipo, distancia = clasificar_obstaculo(bboxes, ROI_HEIGHT)
            else:
                hay_obs, contornos, bboxes = detectar_contornos(binaria)
                tipo, distancia = clasificar_obstaculo(bboxes, ROI_HEIGHT)
                pixeles = cv2.countNonZero(binaria)

            # ── FPS ──
            fps_contador += 1
            ahora = time.time()
            if ahora - fps_tiempo >= 1.0:
                fps_actual   = fps_contador
                fps_contador = 0
                fps_tiempo   = ahora

            metricas[metodo_actual].registrar(hay_obs, fps_actual)

            # ── Visualización ──
            frame_vis, roi_vis = dibujar_info(
                frame, roi, binaria, metodo_actual, fps_actual,
                hay_obs, tipo, distancia, pixeles, bboxes
            )

            binaria_bgr = cv2.cvtColor(binaria, cv2.COLOR_GRAY2BGR)

            cv2.imshow("Frame + deteccion", frame_vis)
            cv2.imshow("ROI con marcadores", roi_vis)
            cv2.imshow("ROI binarizada",     binaria_bgr)

            # ── Teclas ──
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord('q'):
                break
            elif tecla == ord('m'):
                metodo_actual = 2 if metodo_actual == 1 else 1
                print(f"[Método] Cambiado a: {'Conteo de píxeles' if metodo_actual == 1 else 'Contornos'}")

    # Reporte final de ambos métodos
    for m in metricas.values():
        m.reporte()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
