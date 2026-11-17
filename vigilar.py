"""
Vigilante de turnos - Validez Nacional de Títulos (Argentina)

Revisa la página de turnos varias veces (una por minuto) y, si detecta que
YA NO aparece el cartel de "no hay turnos", te manda una notificación al móvil
a través de ntfy.

No hace falta tocar nada de este archivo. La configuración está en los
"Secrets" de GitHub (ver la guía).
"""

import os
import sys
import time
import urllib.request
import urllib.error

URL = "https://titulosvalidez.educacion.gob.ar/validez/detitulos/"

# Cuántas revisiones hace en cada ejecución y cada cuántos segundos.
# GitHub lanza este script cada 5 minutos, así que 5 revisiones x 60 s
# equivalen a revisar más o menos cada minuto.
REVISIONES = int(os.environ.get("REVISIONES", "5"))
ESPERA_SEGUNDOS = int(os.environ.get("ESPERA_SEGUNDOS", "60"))

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
MODO_PRUEBA = os.environ.get("MODO_PRUEBA", "false").lower() == "true"

TEXTO_SIN_TURNOS = "no hay turnos disponibles"


def avisar(titulo, mensaje, prioridad="urgent", etiquetas="rotating_light"):
    """Envía una notificación al móvil mediante ntfy."""
    if not NTFY_TOPIC:
        print("ERROR: falta el secret NTFY_TOPIC. No puedo avisarte.")
        sys.exit(1)
    peticion = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=mensaje.encode("utf-8"),
        headers={
            "Title": titulo.encode("utf-8"),
            "Priority": prioridad,
            "Tags": etiquetas,
            "Click": URL,  # al tocar la notificación se abre la web de turnos
        },
        method="POST",
    )
    urllib.request.urlopen(peticion, timeout=20)
    print(f"Notificación enviada: {titulo}")


def hay_turnos():
    """
    Devuelve True si parece que hay turnos, False si no los hay,
    o None si la página no respondió bien (en ese caso no avisamos,
    para no darte falsas alarmas).
    """
    peticion = urllib.request.Request(
        URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0 Safari/537.36"
            ),
            "Cache-Control": "no-cache",
        },
    )
    try:
        with urllib.request.urlopen(peticion, timeout=30) as respuesta:
            url_final = respuesta.geturl()
            html = respuesta.read().decode("utf-8", errors="ignore")
            estado = respuesta.status
    except urllib.error.HTTPError as e:
        print(f"La página respondió con error {e.code}. Se ignora esta revisión.")
        return None
    except Exception as e:  # sin conexión, tiempo agotado, etc.
        print(f"No se pudo abrir la página ({e}). Se ignora esta revisión.")
        return None

    print(f"Estado {estado} -> {url_final}")

    if estado != 200 or len(html) < 200:
        print("Respuesta rara o vacía. Se ignora esta revisión.")
        return None

    if "noaccess.php" in url_final or TEXTO_SIN_TURNOS in html.lower():
        return False

    return True


def main():
    if MODO_PRUEBA:
        avisar(
            "Prueba del vigilante de turnos",
            "Si ves esto, las notificaciones funcionan. "
            "Toca aquí para abrir la página de turnos.",
            prioridad="default",
            etiquetas="white_check_mark",
        )
        resultado = hay_turnos()
        print(f"Resultado de la revisión de prueba: {resultado}")
        return

    for i in range(1, REVISIONES + 1):
        print(f"--- Revisión {i}/{REVISIONES} ---")
        resultado = hay_turnos()
        if resultado is True:
            avisar(
                "¡HAY TURNOS DISPONIBLES!",
                "La página de Validez de Títulos ya no muestra el cartel de "
                "'no hay turnos'. Toca aquí y saca el turno YA.",
            )
        elif resultado is False:
            print("Sin turnos por ahora.")
        if i < REVISIONES:
            time.sleep(ESPERA_SEGUNDOS)


if __name__ == "__main__":
    main()
