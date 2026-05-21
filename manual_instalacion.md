# BENEMÉRITA UNIVERSIDAD AUTÓNOMA DE PUEBLA

## VISIÓN Y ANIMACIÓN POR COMPUTADORA

### MANUAL DE INSTALACIÓN Y USO

---

**DINOSAURIO GOOGLE**
**SISTEMA DE VISIÓN POR COMPUTADORA**

---

**ALUMNOS**

- VARGAS TEODORO MARCO ANTONIO
- GÓMEZ FLORES JOSÉ ANTONIO

**PROFESOR**

GUSTAVO EMILIO MENDOZA OLGUÍN

**21 de mayo de 2026**

BENEMÉRITA UNIVERSIDAD AUTÓNOMA DE PUEBLA — 2026

---

## 1. Introducción

Este manual describe los pasos necesarios para instalar, configurar y ejecutar el sistema de automatización visual del juego del dinosaurio de Google (`chrome://dino`). El sistema utiliza técnicas de visión por computadora para capturar la pantalla en tiempo real, detectar obstáculos y controlar el teclado automáticamente sin modificar el código del juego.

---

## 2. Requisitos del Sistema

### 2.1 Hardware

- **Procesador:** Intel Core i3 o superior
- **Memoria RAM:** mínimo 4 GB
- **Pantalla:** resolución mínima 1280 x 720 (probado en 1920 x 1080)
- **Conexión a internet:** necesaria solo para la instalación de dependencias

### 2.2 Software

- **Sistema operativo:** Windows 10 / 11, macOS
- **Python** 3.10 o superior (probado con Python 3.12.8)
- **Google Chrome** (cualquier versión reciente)
- **pip** (incluido con Python)

---

## 3. Instalación

### 3.1 Verificar Python

Abre una terminal (PowerShell o CMD) y ejecuta:

```bash
python --version
```

Debe mostrar Python 3.10 o superior. Si no está instalado, descárgalo desde [python.org](https://python.org)

### 3.2 Instalar dependencias

Ejecuta el siguiente comando en la terminal:

```bash
python -m pip install opencv-python mss numpy pynput Pillow
```

Si tienes múltiples versiones de Python instaladas, usa la ruta completa:

```bash
C:/Users/TuUsuario/AppData/Local/Python/bin/python.exe -m pip install opencv-python mss numpy pynput Pillow
```

> **Nota:** Sustituye `TuUsuario` por tu nombre de usuario de Windows.

### 3.3 Verificar instalación

Comprueba que todas las librerías se instalaron correctamente:

```bash
python -c "import cv2, mss, numpy, pynput; print('Todo OK')"
```

Debe imprimir: `Todo OK`

### 3.4 Descargar el código

Descarga o clona el repositorio del proyecto:

```bash
git clone https://github.com/[usuario]/dino-bot.git
```

O descarga el ZIP desde GitHub y descomprímelo en una carpeta de tu elección.

---

## 4. Estructura del Proyecto

| Archivo | Descripción |
|---|---|
| `01_captura_roi.py` | Módulo 1: captura de pantalla y calibración del ROI |
| `02_deteccion.py` | Módulo 2: detección de obstáculos con dos métodos |
| `03_bot_completo.py` | Módulo 3: bot completo con control de teclado |

---

## 5. Configuración Inicial

### 5.1 Parámetros principales

Al inicio de cada archivo se encuentran las variables de configuración. Los valores predeterminados están calibrados para una pantalla de 1920 x 1080 con Chrome sin pantalla completa:

| Variable | Valor | Descripción |
|---|---|---|
| `GAME_TOP` | 420 | Píxeles desde arriba hasta el área del juego |
| `ROI_LEFT` | 160 | Inicio horizontal del ROI (después del dinosaurio) |
| `DISTANCIA_SALTO` | 45 | Distancia en píxeles a la que el bot salta |
| `COOLDOWN_ACCION` | 0.22 s | Tiempo mínimo entre acciones (evita saltos dobles) |

---

## 6. Ejecución del Sistema

### 6.1 Paso a paso

1. Abre Google Chrome y navega a `chrome://dino`
2. Presiona la barra espaciadora para iniciar el juego
3. Abre una terminal y ejecuta el bot:

```bash
python 03_bot_completo.py
```

4. Regresa a Chrome; el bot comenzará a jugar automáticamente

### 6.2 Controles durante la ejecución

| Tecla | Acción |
|---|---|
| `Q` | Salir del bot y mostrar reporte de métricas en terminal |
| `M` | Cambiar entre Método 1 (píxeles) y Método 2 (contornos) |
| `P` | Pausar o reanudar el bot (el juego sigue corriendo) |
| `R` | Reiniciar las métricas del método activo |

---

## 7. Calibración para Diferentes Resoluciones

Si tu pantalla tiene una resolución diferente a 1920x1080, debes recalibrar los parámetros. Ejecuta el módulo 1 para calibrar:

```bash
python 01_captura_roi.py
```

Presiona la tecla `C` para abrir el modo de calibración con sliders. Ajusta los valores hasta que el rectángulo verde quede justo a la derecha del dinosaurio a la altura de los cactus. Los valores finales mostrados en la terminal deben copiarse a los archivos 02 y 03.

> **Consejo:** El ROI debe comenzar exactamente donde termina el dinosaurio y extenderse hacia la derecha cubriendo la zona donde aparecerán los obstáculos.

---

## 8. Solución de Problemas

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: No module named 'mss'` | Instalar con el Python correcto: `python -m pip install mss` |
| El bot salta inmediatamente al iniciar | Aumentar `ROI_LEFT` para alejar el ROI del dinosaurio |
| El bot no detecta los cactus | Reducir `PIXEL_UMBRAL` o `CONTORNO_AREA_MIN` |
| El bot salta demasiado pronto | Reducir `DISTANCIA_SALTO` (ej. de 250 a 200) |
| El bot choca sin saltar | Aumentar `DISTANCIA_SALTO` (ej. de 250 a 320) |
| Las ventanas de OpenCV no aparecen | Verificar que `opencv-python` está instalado correctamente |

---

## 9. Interpretación de Métricas

Al salir del bot (tecla `Q`), se muestra en la terminal un reporte con las siguientes métricas:

- **FPS promedio:** cuadros por segundo procesados (esperado: 55-70 FPS)
- **Frames totales:** número total de imágenes analizadas
- **Detecciones:** veces que se detectó un obstáculo en el ROI
- **Saltos:** número de veces que el bot presionó espacio
- **Agachadas:** número de veces que el bot presionó flecha abajo

---

## 10. Dependencias y Versiones

| Librería | Versión / Uso |
|---|---|
| Python | 3.12.8 |
| `opencv-python` | Captura, preprocesamiento y visualización |
| `mss` | Captura de pantalla de alta velocidad |
| `numpy` | Operaciones matriciales sobre imágenes |
| `pynput` | Control automático del teclado |
| `Pillow` | Manejo auxiliar de imágenes |
