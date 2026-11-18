import cv2
import os
import requests

DATASET_PATH = "dataset"
nombres_clases = [d for d in os.listdir(DATASET_PATH) if os.path.isdir(os.path.join(DATASET_PATH, d))]

if not os.path.exists("modelo_lbph.xml"):
    print("[ERROR] Primero debes ejecutar 'training.py' para generar el modelo.")
    exit()

face_recognizer = cv2.face.LBPHFaceRecognizer_create()
face_recognizer.read("modelo_lbph.xml")

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

cap = cv2.VideoCapture(0)
print("[INFO] Iniciando cámara. Presiona 'q' para salir.")

autenticado = False
frames_verdes = 0 # Contador para confirmar que el recuadro es verde constantemente

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    if len(faces) == 0:
        frames_verdes = 0 # Si no hay rostro, se reinicia el contador

    for (x, y, w, h) in faces:
        rostro = gray[y:y+h, x:x+w]
        rostro_resized = cv2.resize(rostro, (150, 150), interpolation=cv2.INTER_CUBIC)

        label, confidence = face_recognizer.predict(rostro_resized)

        # UMBRAL MÁS ESTRICTO (MENOR A 60)
        if confidence < 80:
            nombre = nombres_clases[label]
            color = (0, 255, 0)
            texto = f"{nombre} ({int(100 - confidence)}%)"
            
            frames_verdes += 1
            
            # SOLO DA ACCESO SI MANTIENE EL RECUADRO VERDE POR 10 FRAMES
            if frames_verdes >= 10:
                try:
                    requests.post("http://127.0.0.1:5000/api/face_auth", json={"nombre": nombre}, timeout=2)
                    autenticado = True
                    break
                except Exception as e:
                    print("Error al conectar con la web:", e)
        else:
            color = (0, 0, 255) 
            texto = "Desconocido"
            frames_verdes = 0 # Si ve a un desconocido, reinicia el contador

        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        cv2.putText(frame, texto, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    if autenticado:
        break

    cv2.imshow("Reconocimiento Facial LBPH", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

if not autenticado:
    try:
        requests.post("http://127.0.0.1:5000/api/face_failed", timeout=2)
    except Exception:
        pass