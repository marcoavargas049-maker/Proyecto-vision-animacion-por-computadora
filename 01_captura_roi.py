"""
Módulo 1 - Captura de pantalla y visualización del ROI
Bot dinosaurio de Google | Visión y Animación por Computadora

Instrucciones:
  1. Abre Chrome y ve a chrome://dino (o desconecta el internet)
  2. Presiona espacio para iniciar el juego
  3. Ejecuta este script: python 01_captura_roi.py
  4. Ajusta las variables ROI_* si la región no coincide con el dino

Controles:
  Q  — salir
  C  — entrar al modo calibración (ajustar ROI con sliders)
"""

import cv2
import numpy as np
import mss
import mss.tools

# ─────────────────────────────────────────────
#  CONFIGURACIÓN DE LA REGIÓN DE INTERÉS (ROI)
#  Ajusta estos valores según tu resolución.
#  El ROI va justo frente al dinosaurio.
# ─────────────────────────────────────────────
# Posición del juego en pantalla (esquina superior izquierda del navegador)
GAME_TOP    = 510   # píxeles desde arriba hasta la zona del juego
GAME_LEFT   = 0     # píxeles desde la izquierda

# Tamaño del área de captura completa
CAPTURE_W   = 800
CAPTURE_H   = 200

# ROI dentro del área capturada (frente al dinosaurio)
# El dinosaurio suele estar a ~80px del borde izquierdo
ROI_LEFT    = 150    # inicio horizontal del ROI (después del dino)
ROI_WIDTH   = 400   # ancho del ROI (cuánto espacio vigilar)
ROI_TOP     = 60   # inicio vertical del ROI
ROI_HEIGHT  = 90   # alto del ROI

# Umbral para binarización (0-255)
# Valores más altos detectan objetos más oscuros
THRESHOLD   = 127


def build_capture_region():
    """Construye el diccionario de región para mss."""
    return {
        "top":    GAME_TOP,
        "left":   GAME_LEFT,
        "width":  CAPTURE_W,
        "height": CAPTURE_H,
    }


def capturar_frame(sct, region):
    """Captura un frame de la pantalla y lo convierte a BGR para OpenCV."""
    screenshot = sct.grab(region)
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    return frame


def extraer_roi(frame):
    """Recorta la región de interés del frame completo."""
    roi = frame[ROI_TOP:ROI_TOP + ROI_HEIGHT,
                ROI_LEFT:ROI_LEFT + ROI_WIDTH]
    return roi


def binarizar(roi):
    """Convierte la ROI a escala de grises y aplica umbralización."""
    gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, binaria = cv2.threshold(gris, THRESHOLD, 255, cv2.THRESH_BINARY_INV)
    return gris, binaria


def dibujar_roi_en_frame(frame):
    """Dibuja un rectángulo verde sobre el frame indicando la ROI."""
    frame_vis = frame.copy()
    cv2.rectangle(
        frame_vis,
        (ROI_LEFT, ROI_TOP),
        (ROI_LEFT + ROI_WIDTH, ROI_TOP + ROI_HEIGHT),
        (0, 255, 0), 2
    )
    cv2.putText(frame_vis, "ROI", (ROI_LEFT, ROI_TOP - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return frame_vis


def modo_calibracion(frame):
    """
    Pantalla de calibración con sliders para ajustar el ROI en tiempo real.
    Presiona Q para salir de la calibración.
    """
    global ROI_LEFT, ROI_WIDTH, ROI_TOP, ROI_HEIGHT, THRESHOLD

    nombre_ventana = "Calibración ROI"
    cv2.namedWindow(nombre_ventana, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(nombre_ventana, 900, 500)

    cv2.createTrackbar("ROI Left",      nombre_ventana, ROI_LEFT,    CAPTURE_W - 10, lambda v: None)
    cv2.createTrackbar("ROI Width",     nombre_ventana, ROI_WIDTH,   CAPTURE_W,      lambda v: None)
    cv2.createTrackbar("ROI Top",       nombre_ventana, ROI_TOP,     CAPTURE_H - 10, lambda v: None)
    cv2.createTrackbar("ROI Height",    nombre_ventana, ROI_HEIGHT,  CAPTURE_H,      lambda v: None)
    cv2.createTrackbar("Umbral",        nombre_ventana, THRESHOLD,   255,            lambda v: None)

    print("\n[Calibración] Ajusta los sliders y presiona Q para guardar y salir.\n")

    with mss.mss() as sct:
        region = build_capture_region()
        while True:
            frame = capturar_frame(sct, region)

            ROI_LEFT   = cv2.getTrackbarPos("ROI Left",   nombre_ventana)
            ROI_WIDTH  = cv2.getTrackbarPos("ROI Width",  nombre_ventana)
            ROI_TOP    = cv2.getTrackbarPos("ROI Top",    nombre_ventana)
            ROI_HEIGHT = cv2.getTrackbarPos("ROI Height", nombre_ventana)
            THRESHOLD  = cv2.getTrackbarPos("Umbral",     nombre_ventana)

            # Evitar valores cero
            ROI_WIDTH  = max(ROI_WIDTH, 10)
            ROI_HEIGHT = max(ROI_HEIGHT, 10)

            roi = extraer_roi(frame)
            if roi.size == 0:
                continue

            _, binaria = binarizar(roi)
            frame_vis  = dibujar_roi_en_frame(frame)

            # Mostrar binaria al lado del frame
            binaria_bgr = cv2.cvtColor(binaria, cv2.COLOR_GRAY2BGR)
            # Redimensionar binaria para que tenga el mismo alto que frame_vis
            binaria_resized = cv2.resize(binaria_bgr, (ROI_WIDTH, CAPTURE_H))
            combinado = np.hstack([frame_vis, binaria_resized])

            cv2.imshow(nombre_ventana, combinado)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyWindow(nombre_ventana)
    print(f"[Calibración] Valores guardados:")
    print(f"  ROI_LEFT={ROI_LEFT}, ROI_WIDTH={ROI_WIDTH}")
    print(f"  ROI_TOP={ROI_TOP}, ROI_HEIGHT={ROI_HEIGHT}")
    print(f"  THRESHOLD={THRESHOLD}")


def main():
    print("=" * 50)
    print("  Bot Dinosaurio | Módulo 1: Captura + ROI")
    print("=" * 50)
    print("Controles: Q = salir | C = calibración")
    print(f"Región de captura: {CAPTURE_W}x{CAPTURE_H} desde ({GAME_LEFT},{GAME_TOP})")
    print(f"ROI: x={ROI_LEFT}, y={ROI_TOP}, w={ROI_WIDTH}, h={ROI_HEIGHT}\n")

    import time
    fps_tiempo = time.time()
    fps_contador = 0
    fps_actual = 0

    with mss.mss() as sct:
        region = build_capture_region()

        while True:
            frame = capturar_frame(sct, region)
            roi   = extraer_roi(frame)

            if roi.size == 0:
                print("[Aviso] ROI vacía, ajusta los valores.")
                continue

            gris, binaria = binarizar(roi)

            # Calcular FPS
            fps_contador += 1
            ahora = time.time()
            if ahora - fps_tiempo >= 1.0:
                fps_actual   = fps_contador
                fps_contador = 0
                fps_tiempo   = ahora

            # Dibujar ROI y FPS en el frame principal
            frame_vis = dibujar_roi_en_frame(frame)
            cv2.putText(frame_vis, f"FPS: {fps_actual}", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)

            # Convertir imágenes grises a BGR para mostrarlas juntas
            gris_bgr    = cv2.cvtColor(gris,    cv2.COLOR_GRAY2BGR)
            binaria_bgr = cv2.cvtColor(binaria, cv2.COLOR_GRAY2BGR)

            # Mostrar las tres ventanas
            cv2.imshow("Frame completo + ROI", frame_vis)
            cv2.imshow("ROI en gris",          gris_bgr)
            cv2.imshow("ROI binarizada",        binaria_bgr)

            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord('q'):
                print("Saliendo...")
                break
            elif tecla == ord('c'):
                cv2.destroyAllWindows()
                modo_calibracion(frame)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
