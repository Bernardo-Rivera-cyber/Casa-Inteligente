# ---------- IMPORTACIONES  ----------
import re
import subprocess
import threading
import unicodedata
import queue
from datetime import datetime

import requests
import speech_recognition as sr
import pyttsx3
import asyncio
import winsdk.windows.media.control as wmc

import winreg
import os
import glob

# ---------- CONFIGURACIÓN  ----------
NOMBRE = "Steve"
CIUDAD = "Ciudad de México"
NAVEGADOR = "msedge"

APLICACIONES = {
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "calculadora": "calc",
    "bloc de notas": "notepad",
    "edge": "msedge",
    "explorador": "explorer",
    "chrome": "chrome",
    "discord": "discord://",
    "whatsapp": "whatsapp://",
    "steam": "steam",
    "paint": "mspaint",
    "administrador de tareas": "taskmgr",
    "panel de control": "control",
    "configuracion": "ms-settings:",
    "camara": "microsoft.windows.camera:",
    "fotos": "ms-photos:",
    "musica": "mswindowsmusic:",
    "reloj": "ms-clock:",
    "winrar": "winrar",
    "blender": "blender",
}

CLIMAS = {
    0: "despejado", 1: "mayormente despejado", 2: "parcialmente nublado",
    3: "nublado", 45: "con niebla", 48: "con niebla",
    51: "con llovizna", 53: "con llovizna", 55: "con llovizna fuerte",
    61: "con lluvia ligera", 63: "con lluvia", 65: "con lluvia fuerte",
    71: "con nieve", 73: "con nieve", 75: "con nieve intensa",
    80: "con chubascos", 81: "con chubascos", 82: "con chubascos fuertes",
    95: "con tormenta", 96: "con tormenta", 99: "con tormenta fuerte",
}

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

# ---------- VOZ: LISTENER DE FONDO + TTS ----------
_cola_textos = queue.Queue()
_stop_listening = None


def hablar(texto: str) -> None:
    """
    Crea un motor pyttsx3 nuevo por frase y habla de forma SÍNCRONA.
    Evita fugas COM de pyttsx3 que cuelgan el motor tras varias frases.
    El llamador (app.py) decide si quiere ejecutarlo en un hilo aparte.
    """
    if not texto:
        return
    try:
        motor = pyttsx3.init()
        motor.setProperty("rate", 150)
        motor.setProperty("volume", 0.9)
        for v in motor.getProperty("voices"):
            nombre = v.name.lower()
            idiomas = str(getattr(v, "languages", "")).lower()
            if "spanish" in nombre or "es" in idiomas or "es_" in idiomas:
                motor.setProperty("voice", v.id)
                break
        motor.say(texto)
        motor.runAndWait()
        motor.stop()
    except Exception as e:
        print(f"[ERROR TTS] {e}")


def _callback_escucha_fondo(recognizer, audio):
    try:
        texto = recognizer.recognize_google(audio, language="es-ES")
        if texto:
            print(f"[TRANSCRITO] {texto}")
            _cola_textos.put(texto)
    except sr.UnknownValueError:
        pass
    except sr.RequestError as e:
        print(f"[Voz] Error de conexión con Google: {e}")


def iniciar_escucha_fondo():
    global _stop_listening
    if _stop_listening is not None:
        return
    reconocedor = sr.Recognizer()
    microfono = sr.Microphone()
    with microfono as source:
        reconocedor.adjust_for_ambient_noise(source, duration=1)
        print("[INFO] Calibración de ruido completada.")
    _stop_listening = reconocedor.listen_in_background(
        microfono, _callback_escucha_fondo, phrase_time_limit=15
    )
    print("[INFO] Micrófono siempre activo (escucha en segundo plano).")


def detener_escucha_fondo():
    global _stop_listening
    if _stop_listening:
        _stop_listening(wait_for_stop=False)
        _stop_listening = None
        print("[INFO] Micrófono detenido.")


def escuchar() -> str:
    try:
        return _cola_textos.get(timeout=0.5)
    except queue.Empty:
        return ""


# ---------- UTILIDADES  ----------
def limpiar(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    for signo in "?!¡¿.,;:":
        texto = texto.replace(signo, "")
    return texto.strip()


def limpiar_nombre(texto: str) -> str:
    if not texto:
        return ""
    texto = limpiar(texto)
    for nombre in ("steve", "patryck", "este", "step", "stif", "es te"):
        texto = texto.replace(nombre, "").strip()
    return " ".join(texto.split())


# ---------- MÚSICA: SABER QUÉ SUENA  ----------
def que_esta_sonando():
    async def obtener():
        try:
            manager = await wmc.GlobalSystemMediaTransportControlsSessionManager.request_async()
            session = manager.get_current_session()
            if not session:
                return "No hay ninguna canción reproduciéndose."
            props = await session.try_get_media_properties_async()
            if props and props.title:
                artista = props.artist if props.artist else "Artista desconocido"
                return f"Está sonando: {props.title} de {artista}."
            return "No hay ninguna canción reproduciéndose."
        except Exception:
            return "No pude obtener la información de la canción."
    try:
        return asyncio.run(obtener())
    except Exception:
        return "No pude obtener la información de la canción."


def pausar_reanudar():
    subprocess.Popen(
        "powershell -c (New-Object -ComObject WScript.Shell).SendKeys([char]179)",
        shell=True,
    )
    return "Reproducción pausada o reanudada."


def siguiente_cancion():
    subprocess.Popen(
        "powershell -c (New-Object -ComObject WScript.Shell).SendKeys([char]176)",
        shell=True,
    )
    return "Siguiente canción."


def cancion_anterior():
    subprocess.Popen(
        "powershell -c (New-Object -ComObject WScript.Shell).SendKeys([char]177)",
        shell=True,
    )
    return "Canción anterior."


# ---------- APLICACIONES: AYUDAS DE BÚSQUEDA  ----------
def buscar_ruta_en_registro(nombre_exe):
    rutas_registro = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\App Paths"),
    ]
    nombres = [nombre_exe, f"{nombre_exe}.exe"]
    for hive, subkey in rutas_registro:
        for nombre in nombres:
            try:
                clave = winreg.OpenKey(hive, f"{subkey}\\{nombre}")
                ruta, _ = winreg.QueryValueEx(clave, "")
                winreg.CloseKey(clave)
                if os.path.exists(ruta):
                    return ruta
            except (WindowsError, FileNotFoundError):
                continue
    return None


def _buscar_steam():
    """Devuelve la ruta de Steam.exe si existe."""
    candidatos = [
        r"C:\Program Files (x86)\Steam\Steam.exe",
        r"C:\Program Files\Steam\Steam.exe",
    ]
    ruta_reg = buscar_ruta_en_registro("steam")
    if ruta_reg:
        candidatos.insert(0, ruta_reg)
    for ruta in candidatos:
        if ruta and os.path.exists(ruta):
            return ruta
    return None


def _buscar_blender():
    """Devuelve la ruta de blender.exe (incluye carpetas de versión)."""
    ruta_reg = buscar_ruta_en_registro("blender")
    if ruta_reg and os.path.exists(ruta_reg):
        return ruta_reg

    fijas = [
        r"C:\Program Files\Blender Foundation\Blender\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender\blender.exe",
    ]
    for ruta in fijas:
        if os.path.exists(ruta):
            return ruta

    patrones = [
        r"C:\Program Files\Blender Foundation\Blender*\blender.exe",
        r"C:\Program Files (x86)\Blender Foundation\Blender*\blender.exe",
    ]
    for patron in patrones:
        encontrados = sorted(glob.glob(patron), reverse=True)
        for ruta in encontrados:
            if os.path.exists(ruta):
                return ruta
    return None


# ---------- APLICACIONES: ABRIR  ----------
def abrir_aplicacion(orden: str) -> str:
    orden_limpio = limpiar(orden)

    for nombre, comando in APLICACIONES.items():
        if nombre not in orden_limpio:
            continue

        if nombre == "blender":
            ruta_blender = _buscar_blender()
            if ruta_blender:
                try:
                    subprocess.Popen([ruta_blender])
                    return "Abriendo Blender."
                except Exception as e:
                    return f"No pude abrir Blender: {e}"
            return "No encontré Blender. Verifica que esté instalado."

        if nombre == "steam":
            ruta_steam = _buscar_steam()
            if ruta_steam:
                try:
                    subprocess.Popen([ruta_steam])
                    return "Abriendo Steam."
                except Exception as e:
                    return f"No pude abrir Steam: {e}"
            try:
                subprocess.Popen("start steam", shell=True)
                return "Abriendo Steam."
            except Exception as e:
                return f"No pude abrir Steam: {e}"

        if comando.endswith("://") or comando.endswith(":") or ":" in comando:
            try:
                subprocess.Popen(f'start "" "{comando}"', shell=True)
                return "Abriendo " + nombre.capitalize() + "."
            except Exception as e:
                return f"No pude abrir {nombre}: {e}"

        ruta_exe = buscar_ruta_en_registro(comando)
        try:
            if ruta_exe:
                subprocess.Popen([ruta_exe])
            else:
                subprocess.Popen("start " + comando, shell=True)
            return "Abriendo " + nombre.capitalize() + "."
        except Exception as error:
            return f"No pude abrir {nombre}. Error: {error}"

    disponibles = ", ".join(APLICACIONES.keys())
    return "No conozco el programa. Puedo abrir: " + disponibles + "."


# ---------- APLICACIONES: CERRAR  ----------
PROCESOS_CIERRE = {
    "word": ["winword.exe"],
    "excel": ["excel.exe"],
    "powerpoint": ["powerpnt.exe"],
    "calculadora": ["Calculator.exe", "WindowsCalculator.exe", "calc.exe"],
    "bloc de notas": ["notepad.exe"],
    "edge": ["msedge.exe"],
    "explorador": ["explorer.exe"],
    "chrome": ["chrome.exe"],
    "firefox": ["firefox.exe"],
    "spotify": ["spotify.exe"],
    "discord": ["Discord.exe", "Update.exe"],
    "whatsapp": ["WhatsApp.exe"],
    "telegram": ["telegram.exe"],
    "steam": ["steam.exe", "steamwebhelper.exe"],
    "vscode": ["code.exe"],
    "paint": ["mspaint.exe"],
    "blender": ["blender.exe"],
    "administrador de tareas": ["Taskmgr.exe"],
    "panel de control": ["SystemSettings.exe", "control.exe"],
    "configuracion": ["SystemSettings.exe"],
    "camara": ["WindowsCamera.exe"],
    "fotos": ["Microsoft.Photos.exe", "PhotosApp.exe", "Photos.exe"],
    "musica": ["Microsoft.ZuneMusic.exe", "Music.UI.exe"],
    "reloj": ["Microsoft.WindowsAlarms.exe", "Time.exe"],
    "winrar": ["WinRAR.exe", "winrar.exe"],
}

PAQUETES_UWP = {
    "calculadora": "Microsoft.WindowsCalculator",
    "configuracion": "windows.immersivecontrolpanel",
    "camara": "Microsoft.WindowsCamera",
    "fotos": "Microsoft.Windows.Photos",
    "musica": "Microsoft.ZuneMusic",
    "reloj": "Microsoft.WindowsAlarms",
}


def _intentar_taskkill(proceso: str) -> bool:
    try:
        r = subprocess.run(
            f"taskkill /IM {proceso} /F",
            shell=True, capture_output=True, text=True,
        )
        return r.returncode == 0
    except Exception:
        return False


def _intentar_powershell_proceso(nombre_sin_exe: str) -> bool:
    try:
        r = subprocess.run(
            f'powershell -NoProfile -Command "'
            f'Get-Process {nombre_sin_exe} -ErrorAction SilentlyContinue | '
            f'Stop-Process -Force -ErrorAction SilentlyContinue"',
            shell=True, capture_output=True, text=True,
        )
        return r.returncode == 0
    except Exception:
        return False


def _cerrar_uwp_por_paquete(nombre_paquete: str) -> bool:
    try:
        ps = (
            f'powershell -NoProfile -Command "'
            f'Get-Process | Where-Object {{ $_.Path -like \'*{nombre_paquete}*\' }} | '
            f'Stop-Process -Force -ErrorAction SilentlyContinue"'
        )
        subprocess.run(ps, shell=True, capture_output=True, text=True)
        return True
    except Exception:
        return False


def cerrar_aplicacion(orden):
    orden_limpio = limpiar(orden)

    for nombre, procesos in PROCESOS_CIERRE.items():
        if nombre not in orden_limpio:
            continue

        cerrado = False

        for proceso in procesos:
            if _intentar_taskkill(proceso):
                cerrado = True
                break
            nombre_sin_exe = proceso.replace(".exe", "")
            if _intentar_powershell_proceso(nombre_sin_exe):
                cerrado = True
                break

        if not cerrado and nombre in PAQUETES_UWP:
            if _cerrar_uwp_por_paquete(PAQUETES_UWP[nombre]):
                cerrado = True

        if cerrado:
            return f"Cerrando {nombre.capitalize()}."
        return f"No pude cerrar {nombre}. Puede que no esté abierto o necesite permisos."

    return "No sé qué aplicación cerrar."


# ---------- CALCULADORA  ----------
from simpleeval import simple_eval


def calcular(entrada):
    texto = limpiar(entrada)
    texto = texto.replace("más", "+").replace("menos", "-").replace("por", "*").replace("entre", "/")
    expr = re.sub(r"[^0-9+\-*/().\s]", "", texto).strip()
    if not expr or not re.search(r"\d", expr):
        return None
    try:
        resultado = simple_eval(expr)
        if isinstance(resultado, float):
            resultado = int(resultado) if resultado.is_integer() else round(resultado, 4)
        return f"El resultado es {resultado}."
    except Exception:
        return "No entendí la operación."


# ---------- BÚSQUEDA EN INTERNET  ----------
def buscar_en_google(consulta):
    if not consulta:
        return "¿Qué quieres buscar?"
    url = "https://www.google.com/search?q=" + consulta.replace(" ", "+")
    try:
        subprocess.Popen(f'start {NAVEGADOR} "{url}"', shell=True)
        return f"Buscando {consulta} en Google."
    except Exception as e:
        return f"No pude buscar: {e}"


# ---------- MÚSICA: REPRODUCIR  ----------
def reproducir_musica(cancion: str) -> str:
    if not cancion:
        return "¿Qué canción quieres escuchar?"
    busqueda = "https://www.youtube.com/results?search_query=" + cancion.replace(" ", "+")
    try:
        pagina = requests.get(busqueda, timeout=8).text
        pos = pagina.find('"videoId":"') + len('"videoId":"')
        id_video = pagina[pos:pos + 11]
        direccion = "https://www.youtube.com/watch?v=" + id_video
    except Exception:
        direccion = busqueda
    try:
        subprocess.Popen('start ' + NAVEGADOR + ' "' + direccion + '"', shell=True)
        return f"Reproduciendo {cancion} en YouTube."
    except Exception as error:
        return f"No pude reproducir la música. Error: {error}"


# ---------- CLIMA Y FECHA  ----------
def consultar_clima(ciudad: str) -> str:
    if not ciudad:
        ciudad = CIUDAD
    try:
        respuesta = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": ciudad, "count": 1, "language": "es"},
            timeout=8,
        )
        lugares = respuesta.json().get("results")
        if not lugares:
            return "No encontré la ciudad " + ciudad + "."
        lat = lugares[0]["latitude"]
        lon = lugares[0]["longitude"]
        nombre_lugar = lugares[0]["name"]
        respuesta = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code",
                "timezone": "auto",
            }, timeout=8,
        )
        ahora = respuesta.json()["current"]
        temperatura = round(ahora["temperature_2m"])
        humedad = round(ahora["relative_humidity_2m"])
        cielo = CLIMAS.get(ahora["weather_code"], "con cielo variable")
        return (f"En {nombre_lugar} hay {temperatura} grados, {cielo}, "
                f"con {humedad}% de humedad.")
    except Exception:
        return "No pude consultar el clima. Revisa tu conexión."


def decir_hora() -> str:
    ahora = datetime.now()
    momento = "de la mañana" if ahora.hour < 12 else "de la tarde" if ahora.hour < 19 else "de la noche"
    return f"Son las {ahora.strftime('%I:%M')} {momento}."


def decir_fecha() -> str:
    hoy = datetime.now()
    return (f"Hoy es {DIAS[hoy.weekday()]} {hoy.day} de "
            f"{MESES[hoy.month - 1]} de {hoy.year}.")


def saludar() -> str:
    hora = datetime.now().hour
    saludo = "Buenos días" if hora < 12 else "Buenas tardes" if hora < 19 else "Buenas noches"
    return f"{saludo}, soy {NOMBRE}. ¿En qué te puedo ayudar?"


# ---------- CEREBRO  ----------
def pensar(entrada: str):
    orden = limpiar(entrada)
    if not orden:
        return "No escuché nada.", False

    orden_sin_nombre = limpiar_nombre(orden)
    if orden_sin_nombre:
        orden = orden_sin_nombre

    print(f"[PENSAR] Texto procesado: '{orden}'")

    if orden in ("salir", "adios", "hasta luego", "terminar"):
        return "Hasta luego. ¡Que tengas buen día!", True

    if "que esta sonando" in orden or "que cancion" in orden:
        return que_esta_sonando(), False

    if orden.startswith("busca") or "buscar en google" in orden:
        consulta = orden.replace("busca", "").replace("buscar en google", "").strip()
        return buscar_en_google(consulta), False

    if orden.startswith(("cierra", "cerrar", "cerrando")):
        return cerrar_aplicacion(orden), False

    es_mate = bool(
        re.search(r"[+\-*/]", orden) or
        any(k in orden for k in ("cuanto es", "cuanto son", "calcula", "resuelve",
                                  "resultado de", "multiplicado por",
                                  "dividido entre", "dividido por"))
    )
    if es_mate and re.search(r"\d", orden):
        res = calcular(entrada)
        if res:
            return res, False

    if "ayuda" in orden or "que puedes hacer" in orden:
        return ("Puedo abrir y cerrar apps, buscar en Google, decir el clima, "
                "la fecha, operaciones, controlar la música y la domótica."), False

    if orden.startswith(("hola", "buen")):
        return saludar(), False

    if "hora" in orden:
        return decir_hora(), False
    if "fecha" in orden or "que dia es" in orden:
        return decir_fecha(), False

    if "clima" in orden or "temperatura" in orden or "llover" in orden:
        ciudad = orden.split(" en ", 1)[1] if " en " in orden else ""
        return consultar_clima(ciudad), False

    if orden.startswith(("pon", "reproduce")) or "escuchar" in orden:
        cancion = orden
        quito = True
        while quito:
            quito = False
            for p in ("ponme", "pon", "reproduce", "quiero escuchar",
                      "escuchar", "musica de", "musica", "la cancion", "algo de"):
                if cancion.startswith(p):
                    cancion = cancion[len(p):].strip()
                    quito = True
                    break
        return reproducir_musica(cancion), False

    if orden.startswith(("pausa", "pausar", "reanuda", "reanudar")) or orden in ("play", "stop", "detente"):
        return pausar_reanudar(), False
    if orden in ("siguiente", "pasa", "next") or "siguiente cancion" in orden or "pasa la cancion" in orden:
        return siguiente_cancion(), False
    if orden in ("anterior", "atras", "regresa") or "cancion anterior" in orden or "regresa la cancion" in orden:
        return cancion_anterior(), False

    if orden.startswith(("abre", "abrir", "abriendo", "inicia")):
        return abrir_aplicacion(orden), False

    return "No entendí el comando.", False