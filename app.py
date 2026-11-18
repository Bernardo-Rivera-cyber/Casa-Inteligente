import threading
import subprocess
import sys
import os
import atexit
from typing import Dict, Any, Tuple
from flask import Flask, jsonify, render_template, request
import serial
import patrick

app = Flask(__name__)

PUERTO_ARDUINO = "COM5"
BAUDRATE = 9600

IS_AUTHENTICATED = False
CURRENT_USER = ""

arduino_connection = None
try:
    arduino_connection = serial.Serial(PUERTO_ARDUINO, BAUDRATE, timeout=1)
    print(f"Conectado al Arduino en {PUERTO_ARDUINO}")
except Exception as e:
    print(f"No se pudo conectar al Arduino en {PUERTO_ARDUINO}: {e}")

ULTIMA_RESPUESTA_HABLADA = ""

    # ---------- LISTENER DE FONDO (MICRÓFONO SIEMPRE ACTIVO) ----------
patrick.iniciar_escucha_fondo()
atexit.register(patrick.detener_escucha_fondo)


def enviar_comando_arduino(comando: str) -> None:
    if arduino_connection and arduino_connection.is_open:
        try:
            arduino_connection.write(f"{comando}\n".encode("utf-8"))
            print(f"[Arduino] Comando: {comando}")
        except Exception as e:
            print(f"[Arduino] Error: {e}")
    else:
        print(f"[Arduino] Sin conexión: {comando}")


def ejecutar_respuesta_voz(texto: str) -> None:
    global ULTIMA_RESPUESTA_HABLADA
    if texto:
        ULTIMA_RESPUESTA_HABLADA = texto
        threading.Thread(target=patrick.hablar, args=(texto,), daemon=True).start()

# ---------- COMANDOS DE VOZ PARA LA CASA ----------
def procesar_comandos_arduino_por_texto(texto_escuchado: str) -> Tuple[bool, str]:
    texto = patrick.limpiar(texto_escuchado)

    # ---------- SERVO: GARAJE ----------
    if any(c in texto for c in [
        "abre la puerta", "abre el garaje", "abrir garaje", "abrir la puerta",
        "abre garaje", "abrir el garaje", "abreme el garaje", "abreme la puerta"
    ]):
        enviar_comando_arduino("abrir garaje")
        return True, "Abriendo la puerta del garaje."

    if any(c in texto for c in [
        "cierra la puerta", "cierra el garaje", "cerrar garaje", "cerrar la puerta",
        "cierra garaje", "cerrar el garaje", "cierrame el garaje", "cierrame la puerta"
    ]):
        enviar_comando_arduino("cerrar garaje")
        return True, "Cerrando la puerta del garaje."

    # ---------- LED GARAJE ----------
    if any(c in texto for c in [
        "enciende el garaje", "prende el garaje", "encender garaje",
        "prender garaje", "enciende garaje", "prende garaje",
        "enciende la luz del garaje", "prende la luz del garaje"
    ]):
        enviar_comando_arduino("encender garaje")
        return True, "Encendiendo la luz del garaje."

    if any(c in texto for c in [
        "apaga el garaje", "apagar garaje", "apaga garaje",
        "apaga la luz del garaje", "apagar la luz del garaje"
    ]):
        enviar_comando_arduino("apagar garaje")
        return True, "Apagando la luz del garaje."

    # ---------- SALA (pin 6, lógica invertida en el .ino) ----------
    if any(c in texto for c in [
        "enciende la sala", "prende la sala", "encender sala", "prender sala",
        "enciende sala", "prende sala", "enciende la luz de la sala",
        "prende la luz de la sala", "encender la sala"
    ]):
        enviar_comando_arduino("encender sala")
        return True, "Encendiendo la luz de la sala."

    if any(c in texto for c in [
        "apaga la sala", "apagar sala", "apaga sala",
        "apaga la luz de la sala", "apagar la luz de la sala"
    ]):
        enviar_comando_arduino("apagar sala")
        return True, "Apagando la luz de la sala."

    # ---------- CUARTO UNO ----------
    if any(c in texto for c in [
        "enciende el cuarto uno", "prende el cuarto uno", "encender cuarto uno",
        "prender cuarto uno", "enciende cuarto uno", "prende cuarto uno",
        "enciende cuarto 1", "prende cuarto 1", "encender cuarto 1",
        "enciende la luz del cuarto uno", "prende la luz del cuarto uno"
    ]):
        enviar_comando_arduino("encender cuarto uno")
        return True, "Encendiendo el cuarto uno."

    if any(c in texto for c in [
        "apaga el cuarto uno", "apagar cuarto uno", "apaga cuarto uno",
        "apaga cuarto 1", "apagar cuarto 1", "apaga la luz del cuarto uno"
    ]):
        enviar_comando_arduino("apagar cuarto uno")
        return True, "Apagando el cuarto uno."

    # ---------- CUARTO DOS ----------
    if any(c in texto for c in [
        "enciende el cuarto dos", "prende el cuarto dos", "encender cuarto dos",
        "prender cuarto dos", "enciende cuarto dos", "prende cuarto dos",
        "enciende cuarto 2", "prende cuarto 2", "encender cuarto 2",
        "enciende la luz del cuarto dos", "prende la luz del cuarto dos"
    ]):
        enviar_comando_arduino("encender cuarto dos")
        return True, "Encendiendo el cuarto dos."

    if any(c in texto for c in [
        "apaga el cuarto dos", "apagar cuarto dos", "apaga cuarto dos",
        "apaga cuarto 2", "apagar cuarto 2", "apaga la luz del cuarto dos"
    ]):
        enviar_comando_arduino("apagar cuarto dos")
        return True, "Apagando el cuarto dos."

    # ---------- BAÑO ----------
    if any(c in texto for c in [
        "enciende el bano", "prende el bano", "encender bano", "prender bano",
        "enciende bano", "prende bano", "enciende el baño", "prende el baño",
        "encender baño", "prender baño", "enciende baño", "prende baño",
        "enciende la luz del bano", "prende la luz del bano",
        "enciende la luz del baño", "prende la luz del baño"
    ]):
        enviar_comando_arduino("encender baño")
        return True, "Encendiendo el baño."

    if any(c in texto for c in [
        "apaga el bano", "apagar bano", "apaga bano",
        "apaga el baño", "apagar baño", "apaga baño",
        "apaga la luz del bano", "apaga la luz del baño"
    ]):
        enviar_comando_arduino("apagar baño")
        return True, "Apagando el baño."

    # ---------- TODO ----------
    if any(c in texto for c in [
        "enciende todo", "prende todo", "encender todo", "prender todo",
        "enciende todas las luces", "prende todas las luces",
        "enciende las luces", "prende las luces"
    ]):
        enviar_comando_arduino("encender todo")
        return True, "Encendiendo todas las luces."

    if any(c in texto for c in [
        "apaga todo", "apagar todo", "apaga todas las luces",
        "apagar todas las luces", "apaga las luces"
    ]):
        enviar_comando_arduino("apagar todo")
        return True, "Apagando todas las luces."

    return False, ""


def construir_respuesta(texto_usuario: str) -> str:
    global ULTIMA_RESPUESTA_HABLADA, IS_AUTHENTICATED

    if not IS_AUTHENTICATED:
        return "Seguridad activa. Primero debes iniciar sesión con tu rostro."

    texto_limpio = patrick.limpiar(texto_usuario)

    # Variantes con las que Google puede transcribir "Steve"
    VARIANTES_NOMBRE = ("steve", "patryck", "esteve", "estev", "step", "stif",
                        "estif", "es te", "esde", "estiben", "esteban")

    # Solo responder si menciona alguna variante del nombre
    if not any(v in texto_limpio for v in VARIANTES_NOMBRE):
        return ""

    # Quitar todas las variantes del nombre del comando
    for nombre in VARIANTES_NOMBRE:
        texto_limpio = texto_limpio.replace(nombre, "").strip()
    texto_limpio = " ".join(texto_limpio.split())

    if not texto_limpio:
        return "¿Sí? ¿En qué te puedo ayudar?"

    # Evitar repetir la misma respuesta
    respuesta_limpia = patrick.limpiar(ULTIMA_RESPUESTA_HABLADA)
    if texto_limpio and respuesta_limpia and (texto_limpio in respuesta_limpia):
        return ""

    # Procesar comando de Arduino
    manejado, resp_arduino = procesar_comandos_arduino_por_texto(texto_limpio)
    if manejado:
        ULTIMA_RESPUESTA_HABLADA = resp_arduino
        return resp_arduino

    # Procesar con patrick
    respuesta_texto, _ = patrick.pensar(texto_limpio)
    ULTIMA_RESPUESTA_HABLADA = respuesta_texto
    return respuesta_texto

# ---------- RUTAS ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/reset_auth", methods=["POST"])
def reset_auth():
    global IS_AUTHENTICATED, CURRENT_USER
    IS_AUTHENTICATED = False
    CURRENT_USER = ""
    return jsonify({"status": "ok"})


@app.route("/api/apps", methods=["GET"])
def obtener_apps():
    return jsonify({"apps": list(patrick.APLICACIONES.keys())})


@app.route("/api/face_login", methods=["POST"])
def face_login():
    global IS_AUTHENTICATED
    IS_AUTHENTICATED = False
    try:
        carpeta_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_script = os.path.join(carpeta_actual, "recognize.py")
        subprocess.Popen([sys.executable, ruta_script])
        return jsonify({"status": "ok", "mensaje": "Iniciando reconocimiento facial..."})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": f"Error: {e}"})


@app.route("/api/face_auth", methods=["POST"])
def face_auth():
    global IS_AUTHENTICATED, CURRENT_USER
    datos = request.get_json() or {}
    nombre = datos.get("nombre", "")
    if nombre:
        IS_AUTHENTICATED = True
        CURRENT_USER = nombre
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"})


@app.route("/api/face_failed", methods=["POST"])
def face_failed():
    global IS_AUTHENTICATED
    IS_AUTHENTICATED = False
    return jsonify({"status": "denied"})


@app.route("/api/auth_status", methods=["GET"])
def auth_status():
    return jsonify({"authenticated": IS_AUTHENTICATED, "user": CURRENT_USER})


@app.route("/api/logout", methods=["POST"])
def logout():
    global IS_AUTHENTICATED, CURRENT_USER
    IS_AUTHENTICATED = False
    CURRENT_USER = ""
    return jsonify({"status": "ok"})


# ---------- CONTROL DE LA CASA (FRONTEND)  ----------
@app.route("/api/house", methods=["POST"])
def control_house():
    datos = request.get_json() or {}
    accion = datos.get("accion", "")
    hab = datos.get("habitacion", "").strip().lower()
    respuesta_texto = ""

    if accion == "abrir_garaje":
        enviar_comando_arduino("abrir garaje")
        respuesta_texto = "Abriendo el garaje."
    elif accion == "cerrar_garaje":
        enviar_comando_arduino("cerrar garaje")
        respuesta_texto = "Cerrando el garaje."
    elif accion == "encender_todo":
        enviar_comando_arduino("encender todo")
        respuesta_texto = "Encendiendo todas las luces."
    elif accion == "apagar_todo":
        enviar_comando_arduino("apagar todo")
        respuesta_texto = "Apagando todas las luces."
    elif accion == "encender_habitacion":
        comando_hab = _normalizar_habitacion(hab)
        if comando_hab:
            enviar_comando_arduino(f"encender {comando_hab}")
            respuesta_texto = f"Encendiendo la luz de {comando_hab}."
        else:
            respuesta_texto = f"No reconozco la habitación: {hab}."
    elif accion == "apagar_habitacion":
        comando_hab = _normalizar_habitacion(hab)
        if comando_hab:
            enviar_comando_arduino(f"apagar {comando_hab}")
            respuesta_texto = f"Apagando la luz de {comando_hab}."
        else:
            respuesta_texto = f"No reconozco la habitación: {hab}."

    if respuesta_texto:
        ejecutar_respuesta_voz(respuesta_texto)

    return jsonify({"status": "ok", "mensaje": respuesta_texto})


def _normalizar_habitacion(hab: str) -> str:
    hab = patrick.limpiar(hab)
    if hab in ("cuarto uno", "cuarto 1"):
        return "cuarto uno"
    if hab in ("cuarto dos", "cuarto 2"):
        return "cuarto dos"
    if hab in ("bano", "baño"):
        return "baño"
    if hab == "sala":
        return "sala"
    if hab == "garaje":
        return "garaje"
    return ""


# ---------- ACCIONES GENERALES  ----------
@app.route("/api/accion", methods=["POST"])
def ejecutar_accion():
    datos: Dict[str, Any] = request.get_json() or {}
    accion = datos.get("accion", "")
    respuesta_texto = ""

    if accion == "saludar":
        respuesta_texto = patrick.saludar()
    elif accion == "abrir_app":
        nombre = datos.get("app", "")
        respuesta_texto = patrick.abrir_aplicacion("abre " + nombre)
    elif accion == "clima_fecha":
        respuesta_texto = patrick.decir_fecha() + " " + patrick.consultar_clima(patrick.CIUDAD)
    else:
        respuesta_texto = "Acción no reconocida."

    if respuesta_texto:
        ejecutar_respuesta_voz(respuesta_texto)
    return jsonify({"status": "ok", "mensaje": respuesta_texto})

 
# ---------- VOZ  ----------
@app.route("/api/voz", methods=["POST"])
def procesar_voz():
    if not IS_AUTHENTICATED:
        return jsonify({"status": "silencio", "escuchado": "", "mensaje": ""})

    texto_escuchado = patrick.escuchar()
    if not texto_escuchado:
        return jsonify({"status": "silencio", "escuchado": "", "mensaje": ""})

    respuesta_texto = construir_respuesta(texto_escuchado)

    if respuesta_texto:
        ejecutar_respuesta_voz(respuesta_texto)
        return jsonify({"status": "ok", "escuchado": texto_escuchado, "mensaje": respuesta_texto})

    return jsonify({"status": "silencio", "escuchado": "", "mensaje": ""})


@app.route("/api/texto", methods=["POST"])
def procesar_texto():
    datos = request.get_json() or {}
    texto = (datos.get("texto", "") or "").strip()
    if not texto:
        return jsonify({"status": "error", "mensaje": "No escribiste ningún comando."})

    respuesta_texto = construir_respuesta(texto)
    if respuesta_texto:
        ejecutar_respuesta_voz(respuesta_texto)
        return jsonify({"status": "ok", "escuchado": texto, "mensaje": respuesta_texto})
    return jsonify({"status": "ok", "escuchado": texto, "mensaje": "Comando ignorado."})


# ---------- REGISTRO DE ROSTROS  ----------
@app.route("/api/add_face", methods=["POST"])
def add_face():
    global IS_AUTHENTICATED, CURRENT_USER

    if not IS_AUTHENTICATED:
        return jsonify({
            "status": "error",
            "mensaje": "Primero debes iniciar sesión con tu rostro para registrar a otro usuario."
        })

    datos = request.get_json() or {}
    nombre = datos.get("nombre", "").strip()

    if not nombre:
        return jsonify({"status": "error", "mensaje": "Escribe un nombre válido."})

    try:
        carpeta_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_script = os.path.join(carpeta_actual, "datasetFace.py")
        subprocess.Popen([sys.executable, ruta_script, nombre])
        return jsonify({
            "status": "ok",
            "mensaje": f"Capturando fotos para {nombre}. Presiona 'q' en la ventana de la cámara cuando termines."
        })
    except Exception as e:
        return jsonify({"status": "error", "mensaje": f"Error: {e}"})


@app.route("/api/entrenar", methods=["POST"])
def entrenar_modelo():
    global IS_AUTHENTICATED

    if not IS_AUTHENTICATED:
        return jsonify({
            "status": "error",
            "mensaje": "Debes iniciar sesión primero."
        })

    try:
        carpeta_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_script = os.path.join(carpeta_actual, "training.py")
        subprocess.Popen([sys.executable, ruta_script])
        return jsonify({
            "status": "ok",
            "mensaje": "Entrenando modelo... espera unos segundos y luego vuelve a iniciar sesión."
        })
    except Exception as e:
        return jsonify({"status": "error", "mensaje": f"Error: {e}"})


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=5000)