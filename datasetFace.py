import cv2
import os
import sys

NOMBRE_USUARIO = sys.argv[1] if len(sys.argv) > 1 else "Usuario"
CARPETA_OUTPUT=f"dataset/{NOMBRE_USUARIO}"
os.makedirs(CARPETA_OUTPUT, exist_ok=True)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

cap = cv2.VideoCapture(0)
count = 0
MAX_FOTOS = 100

print(f"[INFO] Capturando imágenes para {NOMBRE_USUARIO} con OpenCV...")

while cap.isOpened() and count < MAX_FOTOS:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    for (x, y, w, h) in faces:
        rostro = frame[y:y+h, x:x+w]
       
        if rostro.size > 0:
            rostro_resized = cv2.resize(rostro, (160, 160))
            count += 1
           
            file_path = os.path.join(CARPETA_OUTPUT, f"rostro_{count}.jpg")
            cv2.imwrite(file_path, rostro_resized)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"{NOMBRE_USUARIO} - Fotos: {count}/{MAX_FOTOS}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow(f"Captura para {NOMBRE_USUARIO}", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print(f"[INFO] Proceso completado. Se guardaron {count} fotos en '{CARPETA_OUTPUT}'.")